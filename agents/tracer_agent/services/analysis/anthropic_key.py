import os


def anthropic_api_key() -> str:
    try:
        from core.config import get_settings

        return get_settings().ANTHROPIC_API_KEY or ""
    except Exception:
        return os.environ.get("ANTHROPIC_API_KEY", "")
