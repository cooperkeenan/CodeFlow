from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

try:
    ROOT_DIR = Path(__file__).resolve().parents[4]
except IndexError:
    ROOT_DIR = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    ANTHROPIC_API_KEY: str
    GITHUB_CLIENT_ID: str
    GITHUB_CLIENT_SECRET: str

    model_config = SettingsConfigDict(env_file=str(ROOT_DIR / ".env"), case_sensitive=True,  extra="ignore")


@lru_cache
def get_settings() -> Settings:
    return Settings()