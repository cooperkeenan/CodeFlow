from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

try:
    ROOT_DIR = Path(__file__).resolve().parents[3]
except IndexError:
    ROOT_DIR = Path(__file__).resolve().parents[1]


class Settings(BaseSettings):
    ANTHROPIC_API_KEY: str
    TRACER_CHUNK_TOKEN_BUDGET: int = 45000
    TRACER_CHUNK_MAX_COMPONENTS: int = 40
    TRACER_MAX_CONCURRENCY: int = 4
    DATABASE_URL: str = ""

    model_config = SettingsConfigDict(
        env_file=str(ROOT_DIR / ".env"),
        case_sensitive=True,
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()