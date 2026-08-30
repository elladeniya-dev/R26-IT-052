from sqlalchemy.orm import Session

from app.core.exceptions import BrandNotFoundError, ProductNotFoundError
from app.models import Brand, Product
from app.repositories.observation_repo import ObservationRepository
from app.repositories.product_repo import ProductRepository


class ProductService:
    def __init__(self, db: Session):
        self.db = db
        self.products = ProductRepository(db)
        self.observations = ObservationRepository(db)

    def get_product(self, product_id: str) -> tuple[Product, list]:
        product = self.products.get_by_id(product_id)
        if not product:
            raise ProductNotFoundError(f"No product with id '{product_id}'")
        return product, self.products.get_attributes(product_id)

    def list_products(self, **filters) -> tuple[list[Product], int]:
        return self.products.list_products(**filters)

    def get_history(self, product_id: str) -> dict:
        product = self.products.get_by_id(product_id)
        if not product:
            raise ProductNotFoundError(f"No product with id '{product_id}'")
        lifecycle = self.products.get_lifecycle(product_id)
        history = self.observations.get_price_history(product_id)
        return {
            "product_id": product_id,
            "first_seen": product.first_seen,
            "last_seen": lifecycle.last_seen if lifecycle else None,
            "is_still_listed": bool(lifecycle.is_still_listed) if lifecycle else False,
            "history": history,
        }

    def get_brand(self, slug: str) -> Brand:
        brand = self.products.get_brand_by_slug(slug)
        if not brand:
            raise BrandNotFoundError(f"No brand with slug '{slug}'")
        return brand

    def list_brands(self) -> list[Brand]:
        return self.products.list_brands()
