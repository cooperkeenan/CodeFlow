import logging
from pathlib import Path

from shared.code_store.code_store import CodeStore

logger = logging.getLogger(__name__)

_LANGUAGE_MAP: dict[str, str] = {
    ".py": "python",
    ".js": "javascript",
    ".ts": "typescript",
    ".jsx": "javascript",
    ".tsx": "typescript",
    ".go": "go",
    ".rs": "rust",
    ".java": "java",
    ".rb": "ruby",
    ".cs": "csharp",
    ".cpp": "cpp",
    ".c": "c",
    ".sh": "shell",
}


def _infer_language(file_path: str) -> str:
    suffix = Path(file_path).suffix.lower()
    return _LANGUAGE_MAP.get(suffix, suffix.lstrip(".") or "text")


class SourcePersistService:
    def __init__(self, code_store: CodeStore) -> None:
        self._code_store = code_store

    async def persist(self, repo_name: str, temp_dir: str, file_paths: list[str]) -> None:
        try:
            for abs_path in file_paths:
                try:
                    content = Path(abs_path).read_text(errors="replace")
                    rel_path = Path(abs_path).relative_to(temp_dir).as_posix()
                    language = _infer_language(abs_path)
                    await self._code_store.put_file(repo_name, rel_path, language, content)
                except Exception as exc:
                    logger.warning("Failed to persist %s: %s", abs_path, exc)
        except Exception as exc:
            logger.warning("SourcePersistService.persist failed: %s", exc)
