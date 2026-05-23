from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Literal


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    anthropic_api_key: str = "mock-key"
    ingest_mode: Literal["live", "mock"] = "mock"
    classifier_mode: Literal["live", "mock"] = "mock"
    database_url: str = f"sqlite:////tmp/jobs.db"
    max_posting_age_days: int = 30
    min_trust_score: int = 70


settings = Settings()
