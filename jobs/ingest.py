"""Ingests trend-data-collector/output/run_*/*_garments.json into the normalized schema.
Usage: python jobs/ingest.py [--latest-only]. See docs/trend-engine-guide.html."""
from __future__ import annotations

import glob
import os
import re
import sys
import time
from datetime import date, datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.database import SessionLocal  # noqa: E402
from app.ml.category_map import map_category  # noqa: E402
from app.models import Brand, Observation, Product, ProductAttribute  # noqa: E402
from app.repositories.run_repo import RunRepository  # noqa: E402
from sqlalchemy import select  # noqa: E402
from sqlalchemy.dialects.postgresql import insert as pg_insert  # noqa: E402

RUN_DIR_RE = re.compile(r"run_(\d{4}-\d{2}-\d{2})_(\d{2})(\d{2})(\d{2})$")

INAPPROPRIATE_KEYWORDS = [
    "underwear", "nighty", "lingerie", "swimwear", "bikini", "bra",
    "panty", "panties", "sleepwear", "pajamas", "pyjamas", "lounge",
    "boxers", "briefs", "thong", "swimsuit", "bodysuit", "nightwear", "knickers",
]

KNOWN_MATERIALS = {
    "cotton", "linen", "denim", "silk", "satin", "chiffon", "velvet", "leather",
    "lace", "knit", "jersey", "viscose", "rayon", "nylon", "spandex", "crepe",
    "polyester", "wool", "cashmere", "corduroy", "suede", "organza", "tulle",
    "georgette", "modal", "fleece", "twill", "canvas", "chambray", "lycra",
    "cotton blend", "faux leather", "vegan leather", "tencel", "rib fabric",
    "ribbed", "ponte", "scuba", "neoprene", "elastane",
}

KNOWN_COLORS = {
    "black", "white", "red", "blue", "green", "yellow", "purple", "pink",
    "orange", "brown", "grey", "gray", "navy", "maroon", "burgundy", "teal",
    "mustard", "olive", "beige", "cream", "ivory", "coral", "magenta", "cyan",
    "lavender", "lilac", "indigo", "turquoise", "gold", "silver", "khaki",
    "nude", "blush", "rust", "camel", "mint", "sage", "wine", "cobalt", "aqua",
    "charcoal", "peach", "fuchsia", "rose", "tan", "copper", "amber", "jade",
    "ecru", "off-white", "stone", "sand", "lemon", "lime", "denim",
    "acid", "pastel", "dark", "light", "bright", "deep",
}

GARBAGE_PATTERNS = [
    re.compile(r"^\d+$"),
    re.compile(r"^[A-F0-9]{8}-[A-F0-9]{4}", re.IGNORECASE),
    re.compile(r"^[a-f0-9]{6,}$", re.IGNORECASE),
    re.compile(r"^(week|collection|season|vol|no\.?)\s", re.IGNORECASE),
    re.compile(r"^\d{4}$"),
    re.compile(r"^[A-Z0-9\-]{6,}$"),
    re.compile(r"^uk\s?\d+", re.IGNORECASE),
    re.compile(r"^us\s?\d+", re.IGNORECASE),
    re.compile(r"^\d+(xs|s|m|l|xl|xxl)$", re.IGNORECASE),
    re.compile(r"^(xs|s|m|l|xl|xxl|xxxl)$", re.IGNORECASE),
]

KNOWN_SLEEVE_TYPES = sorted([
    "sleeveless", "cap sleeve", "short sleeve", "3/4 sleeve", "elbow sleeve",
    "long sleeve", "puff sleeve", "bell sleeve", "bishop sleeve",
], key=len, reverse=True)

KNOWN_NECKLINES = sorted([
    "crew neck", "round neck", "v neck", "v-neck", "square neck",
    "off shoulder", "off-shoulder", "halter neck", "halter", "sweetheart neckline",
    "boat neck", "collar", "turtleneck", "cowl neck",
], key=len, reverse=True)

KNOWN_SILHOUETTES = sorted([
    "a-line", "a line", "bodycon", "wrap", "shift dress", "empire waist",
    "fit and flare", "asymmetric",
], key=len, reverse=True)

SOURCE_TIER = {
    "tier1_shopify_json": 1,
    "tier2_json_ld": 2,
    "tier2_static_detail": 3,
    "tier3_smart_dom": 4,
    "tier3_autonomous_ai_gemini": 4,
}


def parse_run_date(run_dir: str) -> date:
    name = os.path.basename(run_dir.rstrip("/\\"))
    m = RUN_DIR_RE.search(name)
    if not m:
        raise ValueError(f"Cannot parse date from run folder name: {name}")
    date_part, hh, mm, ss = m.groups()
    return datetime.strptime(f"{date_part} {hh}:{mm}:{ss}", "%Y-%m-%d %H:%M:%S").date()


def is_inappropriate(garment: dict) -> bool:
    title = garment.get("title", "").lower()
    ptype = garment.get("product_type", "").lower()
    tags = [str(t).lower() for t in garment.get("shopify_tags", [])]
    combined = f"{title} {ptype} {' '.join(tags)}"
    return any(k in combined for k in INAPPROPRIATE_KEYWORDS)


def clean_title(title: str) -> str:
    title = re.sub(r"\s[-–]\s?[A-Z]{0,3}\d{3,}[A-Z]?\s*$", "", title, flags=re.IGNORECASE)
    title = re.sub(r"\s\d{5,}\s*$", "", title)
    title = re.sub(r"#\w+", "", title)
    title = re.sub(r"\s[-–]\s?UK\s?\d+\s*$", "", title, flags=re.IGNORECASE)
    return title.strip()


def extract_image_name(image_url: str) -> str:
    if not image_url:
        return ""
    try:
        path = image_url.split("?")[0]
        filename = path.split("/")[-1]
        name = re.sub(r"\.(jpe?g|png|webp|gif)$", "", filename, flags=re.IGNORECASE)
        name = re.sub(r"[-_]", " ", name)
        name = re.sub(r"\b\d{7,}\b", "", name)
        return name.strip()
    except Exception:
        return ""


def is_valid_color(value: str) -> bool:
    if not value or len(value.strip()) < 2:
        return False
    for pattern in GARBAGE_PATTERNS:
        if pattern.match(value.strip()):
            return False
    words = value.lower().split()
    if len(words) > 4:
        return False
    if any(len(w) > 14 for w in words):
        return False
    for word in words:
        if re.sub(r"[^a-z]", "", word) in KNOWN_COLORS:
            return True
    return False


def scan_text_for_color(text: str) -> str | None:
    words = text.lower().split()
    clean = [re.sub(r"[^a-z]", "", w) for w in words if re.sub(r"[^a-z]", "", w)]
    for i in range(len(clean) - 1):
        phrase = f"{clean[i]} {clean[i + 1]}"
        if is_valid_color(phrase):
            return phrase
    for w in clean:
        if w in KNOWN_COLORS:
            return w
    for w in clean:
        if len(w) >= 3 and is_valid_color(w):
            return w
    return None


def extract_color(garment: dict) -> str | None:
    for key in ("desc_color", "variant_color"):
        raw = str(garment.get(key, "")).strip()
        if raw:
            if is_valid_color(raw):
                return raw.lower()
            scanned = scan_text_for_color(raw)
            if scanned:
                return scanned

    tags = [str(t).lower().strip() for t in garment.get("shopify_tags", [])]
    for tag in tags:
        if tag.startswith("color-"):
            candidate = tag.replace("color-", "").strip()
            if is_valid_color(candidate):
                return candidate
    for tag in tags:
        if is_valid_color(tag):
            return tag

    scanned = scan_text_for_color(clean_title(garment.get("title", "")))
    if scanned:
        return scanned

    img_name = extract_image_name(garment.get("primary_image_url", ""))
    if img_name:
        return scan_text_for_color(img_name)
    return None


def extract_material(text: str) -> str | None:
    if not text:
        return None
    value = text.lower()
    pct_matches = re.findall(r"(\d{1,3})\s*%\s*([A-Za-z][A-Za-z\s]{2,20})", value)
    if pct_matches:
        pct_matches.sort(key=lambda m: int(m[0]), reverse=True)
        for _, candidate_text in pct_matches:
            for material in sorted(KNOWN_MATERIALS, key=len, reverse=True):
                if material in candidate_text:
                    return material
    best_pos, best_material = None, None
    for material in KNOWN_MATERIALS:
        pos = value.find(material)
        if pos != -1 and (best_pos is None or pos < best_pos):
            best_pos, best_material = pos, material
    return best_material


def extract_style_attrs(text: str) -> list[tuple[str, str]]:
    """Returns [(attr_type, value), ...] across sleeve_length/neckline/style_detail."""
    if not text:
        return []
    value = text.lower()
    found = []
    for attr_type, vocab in (
        ("sleeve_length", KNOWN_SLEEVE_TYPES),
        ("neckline", KNOWN_NECKLINES),
        ("style_detail", KNOWN_SILHOUETTES),
    ):
        for term in vocab:
            if term in value:
                found.append((attr_type, term))
                break  # only the first/longest match per vocabulary
    return found


def extract_category(garment: dict) -> str:
    ptype = garment.get("product_type", "").lower().strip()
    generic = {"apparel", "clothing", "fashion", "modest wear"}
    if ptype and ptype not in generic:
        raw = ptype.split("_")[-1] if "_" in ptype else ptype
    else:
        raw = garment.get("title", "")
    return map_category(raw)


# --------------------------------------------------------------- DB upserts
def get_or_create_brand(db, slug: str, display_name: str, source_type: str, market_segment: str) -> Brand:
    brand = db.scalar(select(Brand).where(Brand.slug == slug))
    if brand:
        return brand
    brand = Brand(
        slug=slug, display_name=display_name,
        source_tier=SOURCE_TIER.get(source_type, 1), market_segment=market_segment,
    )
    db.add(brand)
    db.flush()
    return brand


def upsert_product(db, product_id: str, brand_id: int, garment: dict, category: str, run_date: date) -> Product:
    product = db.get(Product, product_id)
    image_array = garment.get("image_array") or []
    if product is None:
        product = Product(
            product_id=product_id, brand_id=brand_id, title=garment.get("title", "Unknown"),
            category=category, raw_product_type=garment.get("product_type"),
            product_url=garment.get("product_url"), image_url=garment.get("primary_image_url"),
            published_date=None, num_images=len(image_array),
            has_rich_desc=bool(str(garment.get("description", "")).strip()),
            source_tier=SOURCE_TIER.get(garment.get("source_type", ""), 1),
            first_seen=run_date,
        )
        db.add(product)
    else:
        product.title = garment.get("title", product.title)
        product.category = category
        product.image_url = garment.get("primary_image_url") or product.image_url
        product.num_images = len(image_array) or product.num_images
    return product


def upsert_attribute(db, product_id: str, attr_type: str, attr_value: str) -> None:
    stmt = (
        pg_insert(ProductAttribute)
        .values(product_id=product_id, attr_type=attr_type, attr_value=attr_value)
        .on_conflict_do_nothing()
    )
    db.execute(stmt)


def upsert_observation(db, obs_date: date, product_id: str, garment: dict, is_first_seen: bool) -> None:
    price = garment.get("price_lkr")
    compare_at = garment.get("original_price_lkr") or None
    is_on_sale = bool(compare_at and price and compare_at > price)
    stmt = (
        pg_insert(Observation)
        .values(
            obs_date=obs_date, product_id=product_id, price_lkr=price, compare_at_lkr=compare_at,
            rank_position=garment.get("rank_position"), is_on_sale=is_on_sale,
            is_new_arrival=is_first_seen, in_stock=garment.get("in_stock", True),
        )
        .on_conflict_do_update(
            index_elements=["obs_date", "product_id"],
            set_=dict(
                price_lkr=price, compare_at_lkr=compare_at, rank_position=garment.get("rank_position"),
                is_on_sale=is_on_sale, in_stock=garment.get("in_stock", True),
            ),
        )
    )
    db.execute(stmt)


# ------------------------------------------------------------------- runs
def ingest_run(run_dir: str) -> None:
    run_date = parse_run_date(run_dir)
    db = SessionLocal()
    run_repo = RunRepository(db)

    try:
        for file_path in glob.glob(os.path.join(run_dir, "*_garments.json")):
            if "combined" in file_path:
                continue

            import json
            brand_slug = os.path.basename(file_path).replace("_garments.json", "")
            try:
                garments = json.load(open(file_path, "r", encoding="utf-8"))
            except (json.JSONDecodeError, OSError) as e:
                run_repo.record_run(
                    run_date=run_date, brand_id=_ensure_brand_id(db, brand_slug),
                    status="failed", products_seen=0, products_kept=0, error_message=str(e),
                )
                continue

            start = time.monotonic()
            products_seen = len(garments)
            products_kept = 0
            brand = None

            for garment in garments:
                if is_inappropriate(garment):
                    run_repo.log_dropped(
                        run_date=run_date, brand_id=brand.brand_id if brand else None,
                        reason="non_clothing_or_inappropriate", raw_title=garment.get("title"),
                        raw_payload=garment,
                    )
                    continue

                url = garment.get("product_url")
                if not url:
                    run_repo.log_dropped(
                        run_date=run_date, brand_id=brand.brand_id if brand else None,
                        reason="missing_product_url", raw_title=garment.get("title"),
                    )
                    continue

                if brand is None:
                    brand = get_or_create_brand(
                        db, brand_slug, garment.get("source_name", brand_slug),
                        garment.get("source_type", ""), garment.get("market_segment"),
                    )

                native_id = url.rstrip("/").split("/")[-1].split("?")[0] or url
                product_id = f"{brand_slug}:{native_id}"
                is_first_seen = db.get(Product, product_id) is None

                category = extract_category(garment)
                color = extract_color(garment)
                material_text = " ".join([
                    garment.get("title", ""),
                    " ".join(str(t) for t in garment.get("shopify_tags", [])),
                    garment.get("description", ""),
                ])
                fabric = extract_material(str(garment.get("desc_material", "")).strip()) or extract_material(material_text)
                style_attrs = extract_style_attrs(str(garment.get("desc_style", "")).strip())

                upsert_product(db, product_id, brand.brand_id, garment, category, run_date)
                db.flush()

                upsert_attribute(db, product_id, "category", category.lower())
                if color:
                    upsert_attribute(db, product_id, "color", color)
                if fabric:
                    upsert_attribute(db, product_id, "fabric", fabric)
                for attr_type, value in style_attrs:
                    upsert_attribute(db, product_id, attr_type, value)

                upsert_observation(db, run_date, product_id, garment, is_first_seen)
                products_kept += 1

            db.commit()
            duration_ms = int((time.monotonic() - start) * 1000)
            if brand:
                run_repo.record_run(
                    run_date=run_date, brand_id=brand.brand_id, status="success",
                    products_seen=products_seen, products_kept=products_kept, duration_ms=duration_ms,
                )
            print(f"  {brand_slug:<20} seen={products_seen:<4} kept={products_kept:<4} ({duration_ms}ms)")
    finally:
        db.close()


def _ensure_brand_id(db, slug: str) -> int:
    brand = get_or_create_brand(db, slug, slug, "", None)
    db.commit()
    return brand.brand_id


def run(latest_only: bool = False) -> None:
    root = Path(__file__).resolve().parent.parent
    run_folders = sorted(glob.glob(str(root / "trend-data-collector" / "output" / "run_*")))
    if not run_folders:
        print("No run folders found.")
        return

    if latest_only:
        run_folders = [run_folders[-1]]  # already sorted by name, which sorts chronologically

    for run_dir in run_folders:
        print(f"Ingesting {run_dir}...")
        ingest_run(run_dir)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Ingest scraper JSON output into the normalized schema")
    parser.add_argument("--latest-only", action="store_true")
    args = parser.parse_args()
    run(latest_only=args.latest_only)
