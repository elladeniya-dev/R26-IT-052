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
    # MUST contain at least one known color word — no exceptions
    for word in words:
        clean_word = re.sub(r'[^a-z]', '', word)
        if clean_word in KNOWN_COLORS:
            return True
    return False

def fast_raw_extraction(garment):
    """
    Fast-path extraction using structured shopify_tags and title scanning.
    Runs BEFORE NLP to save compute on well-tagged products.
    """
    tags = [str(t).lower().strip() for t in garment.get("shopify_tags", [])]
    ptype = garment.get("product_type", "").lower().strip()
    title = garment.get("title", "")

    color = None
    category = None

    # 1. Explicit color- prefix tags (e.g. "color-burntorange")
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
        words = clean_title(title).lower().split()
        words_clean = [re.sub(r'[^a-z]', '', w) for w in words]
        # Try 2-word phrases first (e.g. "Acid Blue", "Dark Navy")
        for i in range(len(words_clean) - 1):
            phrase = f"{words_clean[i]} {words_clean[i+1]}"
            if is_valid_color(phrase.title()):
                color = phrase.title()
                break
        # Fallback to single words
        if not color:
            for w in words_clean:
                if w in KNOWN_COLORS:
                    color = w.title()
                    break

    # 4. Category from product_type if not generic
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

    tags_str = ", ".join(str(t) for t in tags) if isinstance(tags, list) else str(tags)
    # Include clean image filename as bonus context (e.g. "suzie striped shirt green uk8")
    context_text = f"{title}. Tags: {tags_str}. Type: {ptype}. Image: {img_name}"

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

def import_historical_garments(data_dir: str, latest_only: bool = False, wipe_db: bool = False):
    model = init_nlp_model()
    db: Session = SessionLocal()
    
    if wipe_db:
        print("Wiping existing products table for a fresh NLP import...")
        db.query(Product).delete()
        db.commit()
        
    root_dir = Path(__file__).resolve().parent.parent
    
    run_folders = glob.glob(os.path.join(root_dir, "trend-data-collector", "output", "run_*"))
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
                            # Fallback to Gemini with rate limit handling
                            import time
                            print(f"Unknown attribute combo: {mapping_key}. Asking Gemini...")
                            time.sleep(4) # 15 RPM limit on free tier => 1 request every 4 seconds
                            from scripts.gemini_mapper import map_attributes_with_gemini
                            img_url = garment.get("primary_image_url", "")
                            
                            gemini_res = map_attributes_with_gemini(
                                garment.get("title", ""),
                                final_cat or "Unknown",
                                final_color or "Unknown",
                                final_pattern or "Unknown",
                                img_url
                            )
                        
                        if gemini_res:
                            ml_cat = gemini_res.get("mapped_category")
                            ml_col = gemini_res.get("mapped_color")
                            ml_pat = gemini_res.get("mapped_pattern")
                            
                            # Save mapping to DB
                            new_map = AttributeMapping(
                                attribute_type="composite",
                                raw_value=mapping_key,
                                ml_standardized_value=f"{ml_cat}||{ml_col}||{ml_pat}"
                            )
                            db.add(new_map)
                            # Flush to ensure we don't get unique constraint violations later
                            db.flush()
                            mapping_cache[mapping_key] = (ml_cat, ml_col, ml_pat)
                        else:
                            # If API failed (429 Rate Limit, etc), fallback safely without DB insert
                            # and CACHE IT so we don't keep sleeping 4s for the exact same failing string
                            ml_cat = final_cat if is_cat_valid else "Unknown"
                            ml_col = final_color if is_col_valid else "Unknown"
                            ml_pat = final_pattern if is_pat_valid else "Solid"
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
                    price=garment.get("price_lkr"),
                    currency="LKR",
                    brand=garment.get("source_name"),
                    source=garment.get("source_type"),
                    product_url=url,
                    image_url=garment.get("primary_image_url"),
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
    args = parser.parse_args()
    
    import_historical_garments("historical_data", latest_only=args.latest_only, wipe_db=args.wipe_db)
