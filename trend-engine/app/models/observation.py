from datetime import date

from sqlalchemy import Boolean, Date, ForeignKey, Integer, Numeric
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class Observation(Base):
    __tablename__ = "observations"

    obs_date: Mapped[date] = mapped_column(Date, primary_key=True)
    product_id: Mapped[str] = mapped_column(
        ForeignKey("products.product_id", ondelete="CASCADE"), primary_key=True
    )
    price_lkr: Mapped[float | None] = mapped_column(Numeric(12, 2))
    compare_at_lkr: Mapped[float | None] = mapped_column(Numeric(12, 2))  # original price when on sale
    rank_position: Mapped[int | None] = mapped_column(Integer)
    is_on_sale: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    is_new_arrival: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    in_stock: Mapped[bool | None] = mapped_column(Boolean)
