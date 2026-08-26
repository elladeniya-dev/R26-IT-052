import os
import sys
from pathlib import Path

# Add the project root to sys.path so we can import 'app'
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.core.database import Base, engine
from app.models import Product, ProductTrendMetric, TrendObservation, TrendSignal

def init_db():
    print(f"Connecting to database: {engine.url}")
    print("Creating tables...")
    Base.metadata.create_all(bind=engine)
    print("Tables created successfully!")

if __name__ == "__main__":
    init_db()
