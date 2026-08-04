from pathlib import Path

EXCLUDED_FILES = {"__init__.py", "conftest.py"}
EXCLUDED_DIRS = {"__pycache__", ".venv", "venv", "tests", "test"}


def is_included(file_path: Path) -> bool:
    if file_path.suffix != ".py":
        return False
    if file_path.name in EXCLUDED_FILES:
        return False
    return not any(ex in file_path.parts for ex in EXCLUDED_DIRS)
