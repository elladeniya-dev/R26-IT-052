from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from app.config import settings

# Neon (serverless Postgres) closes idle connections and takes a moment to wake up, so:
#  - pool_pre_ping replaces a dead pooled connection instead of failing the request on it
#  - pool_recycle retires connections before Neon's idle cut-off
#  - connect_timeout makes an unreachable database fail in seconds (the app gives up after 20 s);
#    without it a single request could hang for a minute or more
#  - pool_timeout makes a request wait at most 10 s for a free connection under heavy load
engine = create_engine(
    settings.database_url,
    pool_pre_ping=True,
    pool_recycle=240,
    pool_timeout=10,
    connect_args={"connect_timeout": 8},
)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


class Base(DeclarativeBase):
    pass


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
