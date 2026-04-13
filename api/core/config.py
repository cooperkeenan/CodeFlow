from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

ROOT_DIR = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    GITHUB_CLIENT_ID: str
    GITHUB_CLIENT_SECRET: str
    ANTHROPIC_API_KEY: str
    CORS_ORIGIN: str = "http://localhost:5173"
    PROFILER_AGENT_URL: str = "http://localhost:8002"
    TRACER_AGENT_URL: str = "http://localhost:8003"
    RENDER_AGENT_URL: str = "http://localhost:8004"
    LOCAL_REPO: bool = False
    LOCAL_REPO_PATH: str = ""

    model_config = SettingsConfigDict(
        env_file=str(ROOT_DIR / ".env"),
        case_sensitive=True,
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()  # type: ignore[call-arg]