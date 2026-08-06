from functools import lru_cache
from pathlib import Path

from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

ROOT_DIR = Path(__file__).resolve().parents[2]

_LOCAL_AGENT_URLS = {
    "PROFILER_AGENT_URL": "http://localhost:8002",
    "TRACER_AGENT_URL": "http://localhost:8003",
    "RENDER_AGENT_URL": "http://localhost:8004",
    "LAYOUT_AGENT_URL": "http://localhost:8006",
    "EXPLAIN_AGENT_URL": "http://localhost:8007",
}


class Settings(BaseSettings):
    GITHUB_CLIENT_ID: str
    GITHUB_CLIENT_SECRET: str
    ANTHROPIC_API_KEY: str
    ENVIRONMENT: str = "production"
    CORS_ORIGIN: str = "http://localhost:5173"
    PROFILER_AGENT_URL: str = "http://localhost:8002"
    TRACER_AGENT_URL: str = "http://localhost:8003"
    RENDER_AGENT_URL: str = "http://localhost:8004"
    LAYOUT_AGENT_URL: str = "http://localhost:8006"
    EXPLAIN_AGENT_URL: str = "http://localhost:8007"
    LOCAL_REPO: bool = False
    LOCAL_REPO_PATH: str = ""
    DATABASE_URL: str = ""
    CI_MAX_UPLOAD_MB: int = 50

    model_config = SettingsConfigDict(
        env_file=str(ROOT_DIR / ".env"),
        case_sensitive=True,
        extra="ignore",
    )

    @model_validator(mode="after")
    def _apply_local_environment(self) -> "Settings":
        if self.ENVIRONMENT.strip().lower() == "local":
            for field, url in _LOCAL_AGENT_URLS.items():
                setattr(self, field, url)
        return self


@lru_cache
def get_settings() -> Settings:
    return Settings()  # type: ignore[call-arg]