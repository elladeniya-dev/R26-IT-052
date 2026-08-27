import os
import re
import sys
import json
import uuid
import glob
import argparse
from pathlib import Path
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import text

# Only import GLiNER when the script runs to prevent module loading errors if missing
try:
    from gliner import GLiNER
except ImportError:
    GLiNER = None

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.core.database import SessionLocal
from app.models import Product, AttributeMapping

INAPPROPRIATE_KEYWORDS = [
    "underwear", "nighty", "lingerie", "swimwear", "bikini", "bra", 
    "panty", "panties", "sleepwear", "pajamas", "pyjamas", "lounge", 
    "boxers", "briefs", "thong", "swimsuit", "bodysuit", "nightwear", "knickers"
]

def init_nlp_model():
    if GLiNER is None:
        raise ImportError("gliner is not installed. Please run 'pip install gliner'")
    
    print("Loading GLiNER medium-v2.5 NLP Model...")
    model = GLiNER.from_pretrained("gliner-community/gliner_medium-v2.5")
    print("Model loaded successfully!")
    return model

def is_inappropriate(garment):
    """Filters out non-trend items like underwear, nighties, lingerie."""
    title = garment.get("title", "").lower()
    ptype = garment.get("product_type", "").lower()
    tags = [str(t).lower() for t in garment.get("shopify_tags", [])]
    
    combined_text = f"{title} {ptype} {' '.join(tags)}"
    for keyword in INAPPROPRIATE_KEYWORDS:
        if keyword in combined_text:
            return True
    return False


KNOWN_MATERIALS = {
    "cotton", "linen", "denim", "silk", "satin", "chiffon", "velvet", "leather",
    "lace", "knit", "jersey", "viscose", "rayon", "nylon", "spandex", "crepe",
    "polyester", "wool", "cashmere", "corduroy", "suede", "organza", "tulle",
    "georgette", "modal", "fleece", "twill", "canvas", "chambray", "lycra",
    "cotton blend", "faux leather", "vegan leather", "tencel", "rib fabric",
    "ribbed", "ponte", "scuba", "neoprene", "elastane",
}

# Real fit descriptors are short, categorical phrases — never full sentences.
# Ordered longest-first so "slim fit" matches before a bare "fit" substring would.
KNOWN_FIT_TYPES = sorted([
    "true to size", "regular fit", "relaxed fit", "loose fit", "slim fit",
    "skinny fit", "straight fit", "tailored fit", "flared fit", "bodycon",
    "oversized", "loose", "relaxed", "regular", "fitted", "slim", "skinny",
], key=len, reverse=True)


def normalize_fit_type(text: str):
    """Only accept short, known fit descriptors — reject full-sentence style
    descriptions that got mislabeled as 'Fit:' by some stores' spec sheets."""
    if not text:
        return None
    value = text.lower().strip()
    for fit in KNOWN_FIT_TYPES:
        if fit in value:
            return fit.title()
    return None


def extract_material(text: str):
    """Free, deterministic material extraction from tags/title/description."""
    if not text:
        return None
    value = text.lower()

    # Composition strings (e.g. "70% Cotton, 27% Nylon, 3% Spandex") state the
    # dominant fabric via its percentage — use that, not "longest keyword
    # anywhere in the string" (which would wrongly pick "Spandex" at 3% over
    # "Cotton" at 70%, since it's the longer word).
    pct_matches = re.findall(r"(\d{1,3})\s*%\s*([A-Za-z][A-Za-z\s]{2,20})", value)
    if pct_matches:
        pct_matches.sort(key=lambda m: int(m[0]), reverse=True)
        for _, candidate_text in pct_matches:
            for material in sorted(KNOWN_MATERIALS, key=len, reverse=True):
                if material in candidate_text:
                    return material.title()

    # No percentages found — fall back to the first known material word as it
    # actually appears in the text (leftmost), not sorted by keyword length.
    best_pos, best_material = None, None
    for material in KNOWN_MATERIALS:
        pos = value.find(material)
        if pos != -1 and (best_pos is None or pos < best_pos):
            best_pos, best_material = pos, material
    return best_material.title() if best_material else None


def _call_gemini_mapping(mapping_key: str, garment: dict, raw_cat: str, raw_color: str, raw_pattern: str):
    """Optional, quota-limited refinement on top of the free local mapper. Never required."""
    import time
    from scripts.gemini_mapper import map_attributes_with_gemini

    print(f"Refining via Gemini: {mapping_key}...")
    time.sleep(4)  # 15 RPM limit on free tier => 1 request every 4 seconds
    return map_attributes_with_gemini(
        garment.get("title", ""),
        raw_cat or "Unknown",
        raw_color or "Unknown",
        raw_pattern or "Unknown",
        garment.get("primary_image_url", ""),
    )

# Known real colors — anything the model extracts MUST contain one of these words to be accepted
KNOWN_COLORS = {
    "black", "white", "red", "blue", "green", "yellow", "purple", "pink",
    "orange", "brown", "grey", "gray", "navy", "maroon", "burgundy", "teal",
    "mustard", "olive", "beige", "cream", "ivory", "coral", "magenta", "cyan",
    "lavender", "lilac", "indigo", "turquoise", "gold", "silver", "khaki",
    "nude", "blush", "rust", "camel", "mint", "sage", "wine", "cobalt", "aqua",
    "charcoal", "peach", "fuchsia", "rose", "tan", "copper", "amber", "jade",
    "white", "ecru", "off-white", "stone", "sand", "lemon", "lime", "denim",
    "acid", "pastel", "dark", "light", "bright", "deep"
}

# Hard reject patterns — these are never colors no matter what
GARBAGE_PATTERNS = [
    re.compile(r'^\d+$'),                                           # Pure digits: "2026", "1785473753"
    re.compile(r'^[A-F0-9]{8}-[A-F0-9]{4}', re.IGNORECASE),        # UUIDs
    re.compile(r'^[a-f0-9]{6,}$', re.IGNORECASE),                   # Hex hashes
    re.compile(r'^(week|collection|season|vol|no\.?)\s', re.IGNORECASE),
    re.compile(r'^\d{4}$'),                                          # Years: "2026"
    re.compile(r'^[A-Z0-9\-]{6,}$'),                                # All-caps SKUs: "DL-244A"
    re.compile(r'^uk\s?\d+', re.IGNORECASE),                        # UK sizes: "Uk 16", "UK10"
    re.compile(r'^us\s?\d+', re.IGNORECASE),                        # US sizes: "US 8"
    re.compile(r'^\d+(xs|s|m|l|xl|xxl)$', re.IGNORECASE),          # Size codes: "2XL"
    re.compile(r'^(xs|s|m|l|xl|xxl|xxxl)$', re.IGNORECASE),        # Pure sizes: "XL", "M"
]

def clean_title(title: str) -> str:
    """Strip trailing product codes, SKUs, and hashes before NLP processing — preserve color words."""
    title = re.sub(r'\s[-–]\s?[A-Z]{0,3}\d{3,}[A-Z]?\s*$', '', title, flags=re.IGNORECASE)
    title = re.sub(r'\s\d{5,}\s*$', '', title)
    title = re.sub(r'#\w+', '', title)
    # Strip UK size suffixes only (NOT color words)
    title = re.sub(r'\s[-–]\s?UK\s?\d+\s*$', '', title, flags=re.IGNORECASE)
    return title.strip()

def extract_image_name(image_url: str) -> str:
    """Extract just the clean filename from the image URL for additional NLP context."""
    if not image_url:
        return ""
    try:
        # Get the filename part, strip query params
        path = image_url.split("?")[0]
        filename = path.split("/")[-1]
        # Remove extension and replace separators with spaces
        name = re.sub(r'\.(jpe?g|png|webp|gif)$', '', filename, flags=re.IGNORECASE)
        name = re.sub(r'[-_]', ' ', name)
        # Remove numeric suffixes like timestamps
        name = re.sub(r'\b\d{7,}\b', '', name)
        return name.strip()
    except Exception:
        return ""

def is_valid_color(value: str) -> bool:
    """
    Strict color validator. Only accepts values that:
    1. Pass all garbage regex checks
    2. Contain at least one word from KNOWN_COLORS
    This prevents sizes (Uk 16), codes, and collection names from slipping through.
    """
    if not value or len(value.strip()) < 2:
        return False
    # Reject anything matching garbage patterns
    for pattern in GARBAGE_PATTERNS:
        if pattern.match(value.strip()):
            return False
    # Reject if too many words (e.g., full sentences)
    words = value.lower().split()
    if len(words) > 4:
        return False
    # Reject if any single word is implausibly long for a color name/phrase
    # (e.g. a glued-together slug like "nolimitcottonrangewomensshirt...").
    # No real color word exceeds ~12 characters ("turquoise", "off-white").
    if any(len(w) > 14 for w in words):
        return False
    # MUST contain at least one known color word — no exceptions
    for word in words:
        clean_word = re.sub(r'[^a-z]', '', word)
        if clean_word in KNOWN_COLORS:
            return True

    # Also accept standard CSS3 color names we haven't hand-curated (e.g.
    # "crimson", "burlywood") — recognized via actual color-space matching,
    # not a guess. Widens what counts as "a real color" beyond our ~50-word list.
    from scripts.color_matcher import match_color_by_distance
    for word in words:
        clean_word = re.sub(r'[^a-z]', '', word)
        if len(clean_word) >= 3 and match_color_by_distance(clean_word):
            return True
    return False

def _scan_text_for_color(text: str):
    """Scan free text for a known color word/phrase (2-word phrases like 'Dark Navy' first)."""
    words = text.lower().split()
    words_clean = [re.sub(r'[^a-z]', '', w) for w in words if re.sub(r'[^a-z]', '', w)]
    for i in range(len(words_clean) - 1):
        phrase = f"{words_clean[i]} {words_clean[i+1]}"
        if is_valid_color(phrase.title()):
            return phrase.title()
    for w in words_clean:
        if w in KNOWN_COLORS:
            return w.title()
    for w in words_clean:
        if len(w) >= 3 and is_valid_color(w.title()):
            return w.title()
    return None


def fast_raw_extraction(garment):
    """
    Fast-path extraction using structured shopify_tags, title, and image
    filename scanning. Runs BEFORE NLP to save compute on well-tagged products.
    """
    tags = [str(t).lower().strip() for t in garment.get("shopify_tags", [])]
    ptype = garment.get("product_type", "").lower().strip()
    title = garment.get("title", "")

    color = None
    category = None

    # -1. Store-written spec sheet in the product description (e.g. "Color: Black,
    # White, Sage Green") — the store telling us directly, highest confidence of all.
    desc_color = str(garment.get("desc_color", "")).strip()
    if desc_color:
        if is_valid_color(desc_color.title()):
            color = desc_color.title()
        else:
            color = _scan_text_for_color(desc_color)

    # 0. Store-declared variant color (Shopify product options) — structured,
    # store-authored data, higher confidence than anything text-derived.
    if not color:
        variant_color = str(garment.get("variant_color", "")).strip()
        if variant_color:
            if is_valid_color(variant_color.title()):
                color = variant_color.title()
            else:
                scanned = _scan_text_for_color(variant_color)
                if scanned:
                    color = scanned

    # 1. Explicit color- prefix tags (e.g. "color-burntorange")
    if not color:
        for tag in tags:
            if tag.startswith("color-"):
                candidate = tag.replace("color-", "").strip().title()
                if is_valid_color(candidate):
                    color = candidate
                    break

    # 2. Tag is exactly a known color (e.g. "blue", "dark blue")
    if not color:
        for tag in tags:
            tag_title = tag.title()
            if is_valid_color(tag_title):
                color = tag_title
                break

    # 3. Scan the cleaned title for known color words (e.g. "Sora Tee - White", "Acid Blue")
    if not color:
        color = _scan_text_for_color(clean_title(title))

    # 4. Scan the image filename directly — some stores encode color there
    # and nowhere else (e.g. "...--1--[BURGUNDY]--1785236017.jpeg").
    if not color:
        img_name = extract_image_name(garment.get("primary_image_url", ""))
        if img_name:
            color = _scan_text_for_color(img_name)

    # 5. Category from product_type if not generic
    generic = {"apparel", "clothing", "fashion", "modest wear"}
    if ptype and ptype not in generic:
        category = ptype.split("_")[-1].title() if "_" in ptype else ptype.title()

    return color, None, category  # Pattern handled by NLP

def extract_missing_entities(model, garment, existing_color, existing_pattern, existing_category):
    """
    Zero-Shot NLP fallback — only runs for fields still missing after fast extraction.
    Uses clean title + tags + image filename as context.
    """
    title = clean_title(garment.get("title", ""))
    tags = garment.get("shopify_tags", [])
    ptype = garment.get("product_type", "")
    img_name = extract_image_name(garment.get("primary_image_url", ""))
    description = str(garment.get("description", ""))[:300]
    image_alt = str(garment.get("image_alt_text", ""))

    tags_str = ", ".join(str(t) for t in tags) if isinstance(tags, list) else str(tags)
    # Include clean image filename, alt text, and description as bonus context
    context_text = (
        f"{title}. Tags: {tags_str}. Type: {ptype}. Image: {img_name}. "
        f"Image alt text: {image_alt}. Description: {description}"
    )

    labels_to_extract = []
    if not existing_color:    labels_to_extract.append("color")
    if not existing_pattern:  labels_to_extract.append("pattern")
    if not existing_category: labels_to_extract.append("clothing item")

    if not labels_to_extract:
        return existing_color, existing_pattern, existing_category

    # Threshold at 0.55 for precision — prevents hallucinations
    entities = model.predict_entities(context_text, labels_to_extract, threshold=0.55)

    for entity in entities:
        label = entity["label"].lower()
        text = entity["text"].title()

        if label == "color" and not existing_color:
            if is_valid_color(text):
                existing_color = text
        elif label == "pattern" and not existing_pattern:
            existing_pattern = text
        elif label == "clothing item" and not existing_category:
            existing_category = text

    return existing_color, existing_pattern, existing_category

def ingest_garments(latest_only: bool = False, wipe_db: bool = False, use_gemini: bool = False):
    model = init_nlp_model()
    db: Session = SessionLocal()
    
    if wipe_db:
        print("Wiping existing products table for a fresh NLP import...")
        db.query(Product).delete()
        db.commit()
        
    root_dir = Path(__file__).resolve().parent.parent
    
    run_folders = sorted(glob.glob(os.path.join(root_dir, "trend-data-collector", "output", "run_*")))
    if not run_folders:
        print("No run folders found.")
        return

    if latest_only:
        latest_folder = max(run_folders, key=os.path.getmtime)
        run_folders = [latest_folder]
        print(f"Processing ONLY latest run folder: {latest_folder}")
    else:
        print(f"Processing ALL {len(run_folders)} run folders...")
    
    total_inserted = 0
    total_skipped_dupes = 0
    total_skipped_inappropriate = 0
    seen_in_session = set()
    mapping_cache = {}

    for run_dir in run_folders:
        files = glob.glob(os.path.join(run_dir, "*_garments.json"))
        for file_path in files:
            if 'combined' in file_path: continue
            
            with open(file_path, "r", encoding="utf-8") as f:
                try:
                    garments = json.load(f)
                except json.JSONDecodeError:
                    continue
            
            for garment in garments:
                # 1. Inappropriate Filter (Underwear, Lingerie)
                if is_inappropriate(garment):
                    total_skipped_inappropriate += 1
                    continue
                
                url = garment.get("product_url")
                if not url: continue
                
                item_id = str(uuid.uuid5(uuid.NAMESPACE_URL, url))
                
                if item_id in seen_in_session:
                    total_skipped_dupes += 1
                    continue
                    
                exists = db.query(Product).filter(Product.item_id == item_id).first()
                if exists:
                    seen_in_session.add(item_id)
                    total_skipped_dupes += 1
                    continue
                
                seen_in_session.add(item_id)
                
                # 2. Fast Extraction from Raw Metadata
                raw_color, raw_pattern, raw_cat = fast_raw_extraction(garment)
                material_text = " ".join([
                    garment.get("title", ""),
                    " ".join(str(t) for t in garment.get("shopify_tags", [])),
                    garment.get("description", ""),
                ])
                # Store-written spec sheet wins if present — it's the store telling
                # us the answer directly — but still normalize it to our known
                # material vocabulary so "70% Cotton, 27% Nylon, 3% Spandex" and
                # "100% Cotton" both collapse to "Cotton" instead of fragmenting
                # into distinct trend attributes.
                desc_material_raw = str(garment.get("desc_material", "")).strip()
                material = extract_material(desc_material_raw) or extract_material(material_text)
                # fit_type must be a short categorical descriptor, not a full
                # sentence — some stores' spec sheets mislabel a style summary
                # as "Fit:", so only accept it if it matches known fit vocabulary.
                fit_type = normalize_fit_type(str(garment.get("desc_fit_type", "")).strip())

                # style stays free text (it's inherently descriptive), but cap
                # length so a full product description doesn't become a
                # "trend attribute" that will never repeat across products.
                style_raw = str(garment.get("desc_style", "")).strip()
                style = style_raw if style_raw and len(style_raw) <= 60 else None

                # 3. NLP Fallback for Missing Data
                final_color, final_pattern, final_cat = extract_missing_entities(
                    model, garment, raw_color, raw_pattern, raw_cat
                )
                
                # 4. Standardize to ML Taxonomy using Gemini (if needed)
                ml_cat, ml_col, ml_pat = None, None, None
                
                # Check if they are already exactly in the H&M taxonomy
                from scripts.ml_taxonomy import HM_CATEGORIES, HM_COLORS, HM_PATTERNS
                
                is_cat_valid = final_cat in HM_CATEGORIES if final_cat else False
                is_col_valid = final_color in HM_COLORS if final_color else False
                is_pat_valid = final_pattern in HM_PATTERNS if final_pattern else False
                
                # If they are all valid (or missing which defaults to 'Unknown'/'Solid' anyway)
                # We don't need Gemini.
                if (is_cat_valid or not final_cat) and (is_col_valid or not final_color) and (is_pat_valid or not final_pattern):
                    ml_cat = final_cat if is_cat_valid else "Unknown"
                    ml_col = final_color if is_col_valid else "Unknown"
                    ml_pat = final_pattern if is_pat_valid else "Solid"
                else:
                    # We will check if the specific string combination is already mapped
                    mapping_key = f"{final_cat}_{final_color}_{final_pattern}"
                    
                    if mapping_key in mapping_cache:
                        ml_cat, ml_col, ml_pat = mapping_cache[mapping_key]
                    else:
                        # Look up in DB
                        existing = db.query(AttributeMapping).filter(
                            AttributeMapping.raw_value == mapping_key
                        ).first()
                        
                        if existing:
                            ml_cat, ml_col, ml_pat = existing.ml_standardized_value.split("||")
                            mapping_cache[mapping_key] = (ml_cat, ml_col, ml_pat)
                        else:
                            # Free, local, deterministic mapping first (no API cost, no rate limit).
                            from scripts.local_taxonomy_mapper import map_attributes_locally
                            local_res = map_attributes_locally(final_cat, final_color, final_pattern)
                            ml_cat = final_cat if is_cat_valid else local_res["mapped_category"]
                            ml_col = final_color if is_col_valid else local_res["mapped_color"]
                            ml_pat = final_pattern if is_pat_valid else local_res["mapped_pattern"]

                            local_fully_resolved = ml_cat != "Unknown" and ml_col != "Unknown" and ml_pat != "Solid"

                            if use_gemini and not local_fully_resolved:
                                gemini_res = _call_gemini_mapping(mapping_key, garment, final_cat, final_color, final_pattern)
                                if gemini_res:
                                    ml_cat = gemini_res.get("mapped_category") or ml_cat
                                    ml_col = gemini_res.get("mapped_color") or ml_col
                                    ml_pat = gemini_res.get("mapped_pattern") or ml_pat

                            new_map = AttributeMapping(
                                attribute_type="composite",
                                raw_value=mapping_key,
                                ml_standardized_value=f"{ml_cat}||{ml_col}||{ml_pat}"
                            )
                            db.add(new_map)
                            db.flush()
                            mapping_cache[mapping_key] = (ml_cat, ml_col, ml_pat)
                
                published_at = garment.get("published_at")
                if published_at:
                    try:
                        collected_at = datetime.fromisoformat(published_at.replace("Z", "+00:00"))
                    except ValueError:
                        collected_at = datetime.now()
                else:
                    collected_at = datetime.now()

                product = Product(
                    item_id=item_id,
                    title=garment.get("title", "Unknown"),
                    category=final_cat or "Unknown",
                    color=[final_color] if final_color else [],
                    pattern=final_pattern or "Solid",
                    material=material,
                    fit_type=fit_type,
                    style=[style] if style else [],
                    price=garment.get("price_lkr"),
                    original_price=garment.get("original_price_lkr") or None,
                    currency="LKR",
                    brand=garment.get("source_name"),
                    source=garment.get("source_type"),
                    product_url=url,
                    image_url=garment.get("primary_image_url"),
                    description=garment.get("description") or None,
                    availability=garment.get("in_stock", True),
                    collected_at=collected_at,
                    ml_category=ml_cat,
                    ml_color=ml_col,
                    ml_pattern=ml_pat
                )
                
                db.add(product)
                total_inserted += 1
                
                if total_inserted % 100 == 0:
                    try:
                        db.commit()
                        print(f"Committed {total_inserted} records...")
                    except Exception as e:
                        db.rollback()
                        print(f"Error on batch commit: {e}")

    try:
        db.commit()
    except Exception as e:
        db.rollback()
    
    db.close()
    
    print(f"\n=== Database Ingestion Complete ===")
    print(f"Total Inserted: {total_inserted}")
    print(f"Skipped (Duplicates): {total_skipped_dupes}")
    print(f"Skipped (Inappropriate/Underwear): {total_skipped_inappropriate}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="NLP ETL script to load scraped garments into DB")
    parser.add_argument("--latest-only", action="store_true", help="Process only the most recent daily run folder")
    parser.add_argument("--wipe-db", action="store_true", help="Wipes the products table before importing")
    parser.add_argument("--use-gemini", action="store_true", help="Also call Gemini as a paid refinement step for anything the free local mapper can't resolve (requires GEMINI_API_KEY + quota)")
    args = parser.parse_args()

    ingest_garments(latest_only=args.latest_only, wipe_db=args.wipe_db, use_gemini=args.use_gemini)
