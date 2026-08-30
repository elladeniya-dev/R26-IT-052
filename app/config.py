from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str
    admin_api_key: str = ""

    # ml/engine.py
    trendnet_path: str = "app/ml/weights/outfitiq_trendnet.pt"
    trendnet_window: int = 4
    mrtf_window: int = 6
    mrtf_min_support: int = 8


settings = Settings()
