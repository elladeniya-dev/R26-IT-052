from app.core.database import SessionLocal
from app.models import Product, TrendObservation

def generate_observations():
    db = SessionLocal()
    
    print("Wiping existing observations to prevent duplicates...")
    db.query(TrendObservation).delete()
    db.commit()

    print("Fetching all products from the database...")
    products = db.query(Product).all()
    
    observations = []
    
    for p in products:
        # Create an observation point for Category
        if p.ml_category and p.ml_category != "Unknown":
            observations.append(TrendObservation(
                source_name="ecommerce_scraper",
                source_type="ecommerce",
                attribute_type="category",
                attribute_value=p.ml_category,
                collected_at=p.collected_at
            ))
            
        # Create an observation point for Color
        if p.ml_color and p.ml_color != "Unknown":
            observations.append(TrendObservation(
                source_name="ecommerce_scraper",
                source_type="ecommerce",
                attribute_type="color",
                attribute_value=p.ml_color,
                collected_at=p.collected_at
            ))
            
        # Create an observation point for Pattern
        if p.ml_pattern and p.ml_pattern != "Unknown":
            observations.append(TrendObservation(
                source_name="ecommerce_scraper",
                source_type="ecommerce",
                attribute_type="pattern",
                attribute_value=p.ml_pattern,
                collected_at=p.collected_at
            ))
            
    print(f"Bulk inserting {len(observations)} trend observation data points...")
    db.bulk_save_objects(observations)
    db.commit()
    print("Successfully generated all Trend Observations!")

if __name__ == "__main__":
    generate_observations()
