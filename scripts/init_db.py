import sys
from pathlib import Path

# Add the project root to sys.path so we can import 'app'
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.core.database import Base, engine
# Imported for their side effect of registering with Base.metadata, not used
# directly — create_all() below only creates tables it knows about.
from app.models import Product, ProductTrendMetric, TrendObservation, TrendSignal, AttributeMapping  # noqa: F401

def init_db():
    print(f"Connecting to database: {engine.url}")
    print("Creating tables...")
    Base.metadata.create_all(bind=engine)
    print("Tables created successfully!")

if __name__ == "__main__":
    init_db()
