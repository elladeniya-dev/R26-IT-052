import importlib
import os
import unittest
from unittest import mock

os.environ.setdefault("DATABASE_URL", "sqlite://")
os.environ.setdefault("GOOGLE_CLIENT_ID", "test-client-id")
os.environ.setdefault("JWT_SECRET_KEY", "test-secret")

from fastapi import HTTPException
from jose import jwt
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.models import User


def load_routes(env):
    """Reload the routes module so DEV_AUTH_BYPASS is re-read."""
    with mock.patch.dict(os.environ, env, clear=False):
        from app.routes import auth_routes

        return importlib.reload(auth_routes)


def new_session():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    User.__table__.create(engine)
    return sessionmaker(bind=engine)()


class DevLoginBypassTests(unittest.TestCase):
    def tearDown(self):
        # Leave the module in its default (disabled) state for other tests.
        env = {"DEV_AUTH_BYPASS": "false"}
        os.environ.pop("RENDER", None)
        load_routes(env)

    def test_disabled_by_default_returns_404(self):
        routes = load_routes({"DEV_AUTH_BYPASS": "false"})
        with self.assertRaises(HTTPException) as ctx:
            routes.dev_login(db=new_session())
        self.assertEqual(ctx.exception.status_code, 404)

    def test_enabled_issues_a_valid_token_for_the_dev_user(self):
        routes = load_routes({"DEV_AUTH_BYPASS": "true"})
        result = routes.dev_login(db=new_session())

        self.assertEqual(result["token_type"], "bearer")
        self.assertEqual(result["user"].email, "dev.user@example.com")
        self.assertEqual(result["user"].auth_provider, "dev")

        payload = jwt.decode(
            result["access_token"],
            os.environ["JWT_SECRET_KEY"],
            algorithms=["HS256"],
        )
        self.assertEqual(payload["sub"], str(result["user"].user_id))

    def test_same_dev_user_is_reused(self):
        routes = load_routes({"DEV_AUTH_BYPASS": "true"})
        db = new_session()
        first = routes.dev_login(db=db)["user"].user_id
        second = routes.dev_login(db=db)["user"].user_id
        self.assertEqual(first, second)
        self.assertEqual(db.query(User).count(), 1)

    def test_refuses_to_load_on_render(self):
        with self.assertRaises(RuntimeError):
            load_routes({"DEV_AUTH_BYPASS": "true", "RENDER": "true"})


if __name__ == "__main__":
    unittest.main()
