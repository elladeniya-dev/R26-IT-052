"""
Read-only connection to the "Koji" product catalog — a teammate's separate
Postgres database, not ours. Deliberately isolated from app/core/database.py:
a different Base/engine so Base.metadata.create_all() in app/main.py never
touches this table, and so a same-named "products" table on each side can
never collide.
"""
import os

from sqlalchemy import Boolean, Column, DateTime, Float, String, create_engine
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import declarative_base, sessionmaker

KojiBase = declarative_base()

_koji_engine = None
KojiSessionLocal = None

koji_database_url = os.getenv("KOJI_DATABASE_URL")
if koji_database_url:
    _koji_engine = create_engine(koji_database_url, pool_pre_ping=True)
    KojiSessionLocal = sessionmaker(bind=_koji_engine, autoflush=False, autocommit=False)


class KojiProduct(KojiBase):
    """Maps the teammate's real `products` table — read-only, never written to."""
    __tablename__ = "products"

    item_id = Column(String, primary_key=True)
    title = Column(String)
    category = Column(String)
    subcategory = Column(String)
    color = Column(JSONB)
    style = Column(JSONB)
    brand = Column(String)
    price = Column(Float)
    currency = Column(String)
    image_url = Column(String)
    product_url = Column(String)
    source = Column(String)
    description = Column(String)
    availability = Column(Boolean)
    collected_at = Column(DateTime)


def get_koji_db():
    if KojiSessionLocal is None:
        raise RuntimeError(
            "KOJI_DATABASE_URL is not set — the recommendations feature needs it in .env"
        )
    db = KojiSessionLocal()
    try:
        yield db
    finally:
        db.close()
