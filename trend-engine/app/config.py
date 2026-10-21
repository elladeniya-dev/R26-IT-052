from pathlib import Path

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

# The .env next to the app folder, wherever the server was started from.
ENV_FILE = Path(__file__).resolve().parent.parent / ".env"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=ENV_FILE, extra="ignore")

    database_url: str
    admin_api_key: str = ""

    @field_validator("database_url")
    @classmethod
    def _force_psycopg3(cls, v: str) -> str:
        # requirements.txt ships psycopg (v3), not psycopg2 — a bare
        # "postgresql://" URL defaults to psycopg2 and breaks on any
        # fresh install (e.g. CI) that doesn't happen to have it too.
        if v.startswith("postgresql://"):
            return v.replace("postgresql://", "postgresql+psycopg://", 1)
        return v

    # ml/engine.py
    trendnet_path: str = "app/ml/weights/outfitiq_trendnet.pt"
    trendnet_window: int = 4
    mrtf_window: int = 6
    mrtf_min_support: int = 8


settings = Settings()
