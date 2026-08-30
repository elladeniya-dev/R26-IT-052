from datetime import date

import pandas as pd
from sqlalchemy import select

from app.models import Brand, Observation, Product, ProductAttribute
from app.repositories.base import BaseRepository


class ObservationRepository(BaseRepository):
    def get_price_history(self, product_id: str) -> list[Observation]:
        stmt = (
            select(Observation)
            .where(Observation.product_id == product_id)
            .order_by(Observation.obs_date)
        )
        return list(self.db.scalars(stmt).all())

    def build_ml_panel_inputs(
        self, since: date | None = None
    ) -> tuple[pd.DataFrame, pd.DataFrame]:
        """Returns (attrs_long, presence) — see app.ml.features.build_panel."""
        obs_stmt = (
            select(
                Observation.obs_date.label("date"),
                Observation.product_id,
                Brand.slug.label("brand"),
                Observation.is_on_sale,
            )
            .join(Product, Product.product_id == Observation.product_id)
            .join(Brand, Brand.brand_id == Product.brand_id)
        )
        if since:
            obs_stmt = obs_stmt.where(Observation.obs_date >= since)
        presence = pd.read_sql(obs_stmt, self.db.bind)

        attrs_stmt = (
            select(
                Observation.obs_date.label("date"),
                Observation.product_id,
                Brand.slug.label("brand"),
                ProductAttribute.attr_type,
                ProductAttribute.attr_value.label("attr"),
            )
            .join(Product, Product.product_id == Observation.product_id)
            .join(Brand, Brand.brand_id == Product.brand_id)
            .join(ProductAttribute, ProductAttribute.product_id == Observation.product_id)
        )
        if since:
            attrs_stmt = attrs_stmt.where(Observation.obs_date >= since)
        attrs_long = pd.read_sql(attrs_stmt, self.db.bind)

        return attrs_long, presence
