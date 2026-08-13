from collections.abc import Iterator, Mapping
from dataclasses import dataclass
from pathlib import Path

DEFAULT_SKIP_DIRS = frozenset(
    {
        ".git",
        ".hg",
        ".mypy_cache",
        ".pytest_cache",
        ".tox",
        ".venv",
        "__pycache__",
        "build",
        "dist",
        "node_modules",
        "site-packages",
        "venv",
    }
)

TEST_DIR_NAMES = frozenset({"test", "tests", "testing"})


def _is_test(relative: Path) -> bool:
    if any(part in TEST_DIR_NAMES for part in relative.parts):
        return True
    name = relative.name
    return name.startswith("test_") or name.endswith("_test.py") or name == "conftest.py"


def iter_python_files(
    root: Path,
    include_tests: bool = False,
    skip_dirs: frozenset[str] = DEFAULT_SKIP_DIRS,
) -> Iterator[Path]:
    for path in sorted(root.rglob("*.py")):
        relative = path.relative_to(root)
        if any(part in skip_dirs for part in relative.parts):
            continue
        if not include_tests and _is_test(relative):
            continue
        yield path


def read_sources(
    root: Path,
    include_tests: bool = False,
    skip_dirs: frozenset[str] = DEFAULT_SKIP_DIRS,
) -> Mapping[str, str]:
    """Deterministic {relative_posix_path: source} map."""
    sources: dict[str, str] = {}
    for path in iter_python_files(root, include_tests=include_tests, skip_dirs=skip_dirs):
        try:
            sources[path.relative_to(root).as_posix()] = path.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError):
            continue
    return dict(sorted(sources.items()))


def module_name_for_path(path: Path) -> str:
    """Dotted module name derived from where imports actually resolve.

    Walks up while `__init__.py` exists, so the import root is discovered rather
    than assumed to be the repository root. A repo laid out as `backend/app/...`
    yields `app.api.routes.items`, matching what its own imports reference.
    Assuming repo-root-is-import-root silently breaks every cross-module lookup.
    """
    stem = path.with_suffix("")
    parts: list[str] = [] if stem.name == "__init__" else [stem.name]
    directory = path.parent
    while (directory / "__init__.py").exists():
        parts.append(directory.name)
        directory = directory.parent
    return ".".join(reversed(parts))


@dataclass(frozen=True)
class SourceTree:
    root: Path
    sources: Mapping[str, str]
    modules: Mapping[str, str]

    def __len__(self) -> int:
        return len(self.sources)


def load_tree(
    root: Path,
    include_tests: bool = False,
    skip_dirs: frozenset[str] = DEFAULT_SKIP_DIRS,
) -> SourceTree:
    sources: dict[str, str] = {}
    modules: dict[str, str] = {}
    for path in iter_python_files(root, include_tests=include_tests, skip_dirs=skip_dirs):
        relative = path.relative_to(root).as_posix()
        try:
            sources[relative] = path.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError):
            continue
        modules[relative] = module_name_for_path(path)
    return SourceTree(
        root=root,
        sources=dict(sorted(sources.items())),
        modules=dict(sorted(modules.items())),
    )
