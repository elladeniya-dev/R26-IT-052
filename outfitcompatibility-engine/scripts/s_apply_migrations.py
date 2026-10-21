"""Apply pending, numbered SQL migrations to the Senu database."""

from pathlib import Path
import sys

SERVER_ROOT = Path(__file__).resolve().parents[1]
if str(SERVER_ROOT) not in sys.path:
    sys.path.insert(0, str(SERVER_ROOT))

from sqlalchemy import text

from app.s_database import engine


MIGRATIONS_DIR = SERVER_ROOT / "migrations"


def apply_migrations() -> None:
    with engine.begin() as connection:
        connection.execute(text(
            """
            CREATE TABLE IF NOT EXISTS s_schema_migrations (
                version VARCHAR(255) PRIMARY KEY,
                applied_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
            """
        ))

        applied_versions = set(connection.execute(text(
            "SELECT version FROM s_schema_migrations"
        )).scalars())

        for migration_path in sorted(MIGRATIONS_DIR.glob("*.sql")):
            version = migration_path.stem
            if version in applied_versions:
                print(f"Already applied: {version}")
                continue

            sql = migration_path.read_text(encoding="utf-8")
            connection.exec_driver_sql(sql)
            connection.execute(
                text("INSERT INTO s_schema_migrations (version) VALUES (:version)"),
                {"version": version},
            )
            print(f"Applied: {version}")


if __name__ == "__main__":
    apply_migrations()
