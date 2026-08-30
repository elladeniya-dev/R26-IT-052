"""
Integration-style fixtures against the real database, not SQLite — this
project uses Postgres-specific features throughout (JSONB, native ENUM,
DISTINCT ON), so an in-memory SQLite substitute would silently test a
different set of SQL semantics than what actually runs in production. Each
test runs inside a transaction that's rolled back afterward, so nothing
written by a test persists.
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import sessionmaker

from app.database import engine, get_db
from app.main import app


@pytest.fixture
def db_session():
    connection = engine.connect()
    transaction = connection.begin()
    SessionForTest = sessionmaker(bind=connection)
    session = SessionForTest()
    try:
        yield session
    finally:
        session.close()
        transaction.rollback()
        connection.close()


@pytest.fixture
def client(db_session):
    def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    try:
        yield TestClient(app)
    finally:
        app.dependency_overrides.clear()
