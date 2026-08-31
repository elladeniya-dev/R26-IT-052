from sqlalchemy import func, select

from app.models import Brand, Observation, Product, ProductAttribute, ProductLifecycle
from app.repositories.base import BaseRepository


class ProductRepository(BaseRepository):
    def get_by_id(self, product_id: str) -> Product | None:
        return self.db.get(Product, product_id)

    def get_attributes(self, product_id: str) -> list[ProductAttribute]:
        stmt = select(ProductAttribute).where(ProductAttribute.product_id == product_id)
        return list(self.db.scalars(stmt).all())

    def list_products(
        self,
        *,
        brand_slug: str | None = None,
        category: str | None = None,
        color: str | None = None,
        fabric: str | None = None,
        on_sale: bool | None = None,
        page: int = 1,
        size: int = 20,
    ) -> tuple[list[Product], int]:
        stmt = select(Product).join(Brand, Product.brand_id == Brand.brand_id)
        if brand_slug:
            stmt = stmt.where(Brand.slug == brand_slug)
        if category:
            stmt = stmt.where(Product.category == category)
        if color:
            stmt = stmt.where(
                Product.product_id.in_(
                    select(ProductAttribute.product_id).where(
                        ProductAttribute.attr_type == "color", ProductAttribute.attr_value == color
                    )
                )
            )
        if fabric:
            stmt = stmt.where(
                Product.product_id.in_(
                    select(ProductAttribute.product_id).where(
                        ProductAttribute.attr_type == "fabric", ProductAttribute.attr_value == fabric
                    )
                )
            )
        if on_sale is not None:
            latest_obs = (
                select(Observation.product_id, Observation.is_on_sale)
                .distinct(Observation.product_id)
                .order_by(Observation.product_id, Observation.obs_date.desc())
                .subquery()
            )
            stmt = stmt.join(latest_obs, latest_obs.c.product_id == Product.product_id).where(
                latest_obs.c.is_on_sale.is_(on_sale)
            )

        total = self.db.scalar(select(func.count()).select_from(stmt.subquery())) or 0
        stmt = stmt.order_by(Product.first_seen.desc()).offset((page - 1) * size).limit(size)
        return list(self.db.scalars(stmt).all()), total

    def get_lifecycle(self, product_id: str) -> ProductLifecycle | None:
        return self.db.get(ProductLifecycle, product_id)

    # ---------------------------------------------------- bulk product lookups
    def get_product_ids_for_attribute(self, attr_type: str, attr_value: str, limit: int) -> list[str]:
        stmt = (
            select(ProductAttribute.product_id)
            .join(ProductLifecycle, ProductLifecycle.product_id == ProductAttribute.product_id)
            .where(
                ProductAttribute.attr_type == attr_type,
                ProductAttribute.attr_value == attr_value,
                ProductLifecycle.is_still_listed.is_(True),
            )
            .order_by(ProductLifecycle.rank_best.asc().nulls_last())
            .limit(limit)
        )
        return list(self.db.scalars(stmt).all())

    def get_products_bulk(self, product_ids: list[str]) -> dict[str, Product]:
        if not product_ids:
            return {}
        stmt = select(Product).where(Product.product_id.in_(product_ids))
        return {p.product_id: p for p in self.db.scalars(stmt).all()}

    def get_lifecycles_bulk(self, product_ids: list[str]) -> dict[str, ProductLifecycle]:
        if not product_ids:
            return {}
        stmt = select(ProductLifecycle).where(ProductLifecycle.product_id.in_(product_ids))
        return {lc.product_id: lc for lc in self.db.scalars(stmt).all()}

    def get_attributes_bulk(
        self, product_ids: list[str], attr_types: tuple[str, ...]
    ) -> dict[str, dict[str, list[str]]]:
        if not product_ids:
            return {}
        stmt = select(ProductAttribute).where(
            ProductAttribute.product_id.in_(product_ids), ProductAttribute.attr_type.in_(attr_types)
        )
        out: dict[str, dict[str, list[str]]] = {}
        for attr in self.db.scalars(stmt).all():
            out.setdefault(attr.product_id, {}).setdefault(attr.attr_type.value, []).append(attr.attr_value)
        return out

    def get_brands_bulk(self, brand_ids: set[int]) -> dict[int, Brand]:
        if not brand_ids:
            return {}
        stmt = select(Brand).where(Brand.brand_id.in_(brand_ids))
        return {b.brand_id: b for b in self.db.scalars(stmt).all()}

    # -------------------------------------------------------------- brands
    def get_brand_by_slug(self, slug: str) -> Brand | None:
        return self.db.scalar(select(Brand).where(Brand.slug == slug))

    def get_brand(self, brand_id: int) -> Brand | None:
        return self.db.get(Brand, brand_id)

    def list_brands(self, active_only: bool = True) -> list[Brand]:
        stmt = select(Brand)
        if active_only:
            stmt = stmt.where(Brand.is_active.is_(True))
        return list(self.db.scalars(stmt.order_by(Brand.display_name)).all())

    # -------------------------------------------------------------- stats
    def count_products(self) -> int:
        return self.db.scalar(select(func.count()).select_from(Product)) or 0

    def count_brands(self, active_only: bool = True) -> int:
        stmt = select(func.count()).select_from(Brand)
        if active_only:
            stmt = stmt.where(Brand.is_active.is_(True))
        return self.db.scalar(stmt) or 0

    def get_observation_date_range(self) -> tuple[object | None, object | None]:
        row = self.db.execute(
            select(func.min(Observation.obs_date), func.max(Observation.obs_date))
        ).one()
        return row[0], row[1]

    def count_observations(self) -> int:
        return self.db.scalar(select(func.count()).select_from(Observation)) or 0

    def get_attribute_distribution(self, attr_type: str) -> list[tuple[str, int]]:
        stmt = (
            select(ProductAttribute.attr_value, func.count(func.distinct(ProductAttribute.product_id)))
            .where(ProductAttribute.attr_type == attr_type)
            .group_by(ProductAttribute.attr_value)
            .order_by(func.count(func.distinct(ProductAttribute.product_id)).desc())
        )
        return list(self.db.execute(stmt).all())
