from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

ROOT_DIR = Path(__file__).resolve().parents[2]


class MissingCredential(RuntimeError):
    """Raised instead of silently degrading to a weaker configuration."""


class Settings(BaseSettings):
    ANTHROPIC_API_KEY: str = ""
    CODEFLOW_PATH: Path = ROOT_DIR.parent
    CODEFLOW_REMOTE_URL: str = ""
    JUDGE_PRIMARY_MODEL: str = "claude-opus-5"
    JUDGE_SECONDARY_MODEL: str = "claude-sonnet-5"
    CORPUS_CACHE_DIR: Path = ROOT_DIR / "corpus_cache"
    RESULTS_DIR: Path = ROOT_DIR / "results"
    TRUTH_DIR: Path = ROOT_DIR / "bench" / "truth" / "data"
    JUDGE_CACHE_DIR: Path = ROOT_DIR / ".bench_cache"
    PROBE_VENVS_DIR: Path = ROOT_DIR / ".probe_venvs"

    model_config = SettingsConfigDict(
        env_file=str(ROOT_DIR / ".env"),
        case_sensitive=True,
        extra="ignore",
    )

    def require_anthropic_key(self, purpose: str) -> str:
        if not self.ANTHROPIC_API_KEY.strip():
            raise MissingCredential(
                f"ANTHROPIC_API_KEY is required for {purpose} but is not set.\n"
                "Set it in the environment or benchmark/.env.\n"
                "Refusing to continue: a missing key would silently downgrade the "
                "subject to its heuristic judge and the results would describe a "
                "different system than the one you meant to measure."
            )
        return self.ANTHROPIC_API_KEY.strip()


@lru_cache
def get_settings() -> Settings:
    return Settings()
