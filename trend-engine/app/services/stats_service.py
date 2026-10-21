from datetime import date

from sqlalchemy.orm import Session

from app.repositories.product_repo import ProductRepository


class StatsService:
    def __init__(self, db: Session):
        self.db = db
        self.products = ProductRepository(db)

    def overview(self) -> dict:
        min_date, max_date = self.products.get_observation_date_range()
        freshness_days = (date.today() - max_date).days if max_date else None
        return {
            "total_products": self.products.count_products(),
            "total_brands": self.products.count_brands(active_only=True),
            "total_observations": self.products.count_observations(),
            "date_range": {"start": min_date, "end": max_date},
            "freshness_days": freshness_days,
        }

    def attribute_distribution(self, attr_type: str) -> list[dict]:
        rows = self.products.get_attribute_distribution(attr_type)
        return [{"attr_value": value, "product_count": count} for value, count in rows]
