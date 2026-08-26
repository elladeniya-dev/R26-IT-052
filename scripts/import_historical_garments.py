import os
import sys
import json
import uuid
import glob
import argparse
from pathlib import Path
from datetime import datetime
from sqlalchemy.orm import Session

# Only import GLiNER when the script runs to prevent module loading errors if missing
try:
    from gliner import GLiNER
except ImportError:
    GLiNER = None

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.core.database import SessionLocal
from app.models import Product


def init_nlp_model():
    if GLiNER is None:
        raise ImportError("gliner is not installed. Please run 'pip install gliner'")
    
    # Load GLiNER medium-v2.5 as requested by the user
    print("Loading GLiNER medium-v2.5 NLP Model...")
    model = GLiNER.from_pretrained("urchade/gliner_medium-v2.5")
    print("Model loaded successfully!")
    return model


def extract_entities(model, garment):
    """
    Uses Zero-Shot NLP to extract Color, Pattern, and Category from unstructured text.
    """
    title = garment.get("title", "")
    tags = garment.get("shopify_tags", [])
    ptype = garment.get("product_type", "")
    url = garment.get("primary_image_url", "")
    
    # Construct a natural language string for the model to read contextually
    tags_str = ", ".join(tags) if isinstance(tags, list) else str(tags)
    context_text = f"{title}. Tags: {tags_str}. Type: {ptype}. Image Slug: {url}"
    
    labels = ["color", "pattern", "clothing item"]
    
    # Predict entities using GLiNER
    entities = model.predict_entities(context_text, labels, threshold=0.4)
    
    color, pattern, category = "Unknown", "Solid", "Unknown"
    
    for entity in entities:
        label = entity["label"].lower()
        text = entity["text"].title()
        score = entity["score"]
        
        # Only overwrite if we haven't found a better one (we could use score to tie-break)
        if label == "color" and color == "Unknown":
            color = text
        elif label == "pattern" and pattern == "Solid":
            pattern = text
        elif label == "clothing item" and category == "Unknown":
            category = text
            
    return color, pattern, category


def import_historical_garments(data_dir: str, latest_only: bool = False):
    model = init_nlp_model()
    db: Session = SessionLocal()
    root_dir = Path(__file__).resolve().parent.parent
    
    # Find all daily run folders
    run_folders = glob.glob(os.path.join(root_dir, "trend-data-collector", "output", "run_*"))
    
    if not run_folders:
        print("No run folders found.")
        return
        
    if latest_only:
        # Sort by modification time and just take the absolute latest run
        latest_folder = max(run_folders, key=os.path.getmtime)
        run_folders = [latest_folder]
        print(f"Processing ONLY latest run folder: {latest_folder}")
    else:
        print(f"Processing ALL {len(run_folders)} run folders...")
    
    total_inserted = 0
    total_skipped = 0
    seen_in_session = set()

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
                url = garment.get("product_url")
                if not url: continue
                
                item_id = str(uuid.uuid5(uuid.NAMESPACE_URL, url))
                
                if item_id in seen_in_session:
                    total_skipped += 1
                    continue
                    
                exists = db.query(Product).filter(Product.item_id == item_id).first()
                if exists:
                    seen_in_session.add(item_id)
                    total_skipped += 1
                    continue
                
                seen_in_session.add(item_id)
                
                published_at = garment.get("published_at")
                if published_at:
                    try:
                        collected_at = datetime.fromisoformat(published_at.replace("Z", "+00:00"))
                    except ValueError:
                        collected_at = datetime.now()
                else:
                    collected_at = datetime.now()
                
                # Perform Zero-Shot NLP Extraction
                color, pattern, category = extract_entities(model, garment)

                product = Product(
                    item_id=item_id,
                    title=garment.get("title", "Unknown"),
                    category=category,
                    color=[color] if color != "Unknown" else [],
                    pattern=pattern,
                    price=garment.get("price_lkr"),
                    currency="LKR",
                    brand=garment.get("source_name"),
                    source=garment.get("source_type"),
                    product_url=url,
                    image_url=garment.get("primary_image_url"),
                    collected_at=collected_at
                )
                
                db.add(product)
                total_inserted += 1
                
                if total_inserted % 100 == 0:
                    try:
                        db.commit()
                        print(f"Committed {total_inserted} NLP-standardized records...")
                    except Exception as e:
                        db.rollback()
                        print(f"Error on batch commit: {e}")

    try:
        db.commit()
    except Exception as e:
        db.rollback()
    
    db.close()
    
    print(f"Import complete! Inserted: {total_inserted} | Skipped (Duplicates): {total_skipped}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="NLP ETL script to load scraped garments into DB")
    parser.add_argument("--latest-only", action="store_true", help="Process only the most recent daily run folder")
    args = parser.parse_args()
    
    import_historical_garments("historical_data", latest_only=args.latest_only)
