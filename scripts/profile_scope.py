import asyncio
import sys
from pathlib import Path

import httpx

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "agents" / "profiler_agent"))

from profiler.models.repo_skeleton import RepoSkeleton
from profiler.services.file_tree_service import FileTreeService
from profiler.services.module_detector import ModuleDetector
from profiler.services.repo_map_service import RepoMapService
from render_repo import _is_test_path


def _minimal_dirs(skeleton: RepoSkeleton) -> list[str]:
    dirs = sorted({d.path.rstrip("/") for m in skeleton.modules for d in m.directories})
    if any(d in ("", ".") for d in dirs):
        return [""]
    return [d for d in dirs if not any(o != d and d.startswith(o + "/") for o in dirs)]


def _directory_of(relpath: str) -> str:
    return "/".join(Path(relpath).parts[:-1])


def _in_scope(directory: str, scope_dirs: list[str]) -> bool:
    if "" in scope_dirs:
        return True
    return any(directory == d or directory.startswith(d + "/") for d in scope_dirs)


async def _fetch_paths(repo_path: Path) -> list[str]:
    files = FileTreeService(httpx.AsyncClient())
    return await files.get_tree(local_path=str(repo_path))


def _non_test_py(paths: list[str]) -> list[str]:
    return [p for p in paths if p.endswith(".py") and not _is_test_path(Path(p))]


def main(argv: list[str]) -> int:
    if len(argv) < 2:
        print("usage: profile_scope.py <repo_path>")
        return 1
    repo_path = Path(argv[1]).expanduser().resolve()
    paths = asyncio.run(_fetch_paths(repo_path))
    skeleton = RepoMapService(ModuleDetector()).build(paths, repo_path.name)

    print(f"module roots ({len(skeleton.modules)}):")
    for module in skeleton.modules:
        print(f"  - {module.root_path or '(repo root)'}  is_service={module.is_service}")

    scope_dirs = _minimal_dirs(skeleton)
    print(f"fetch scope dirs: {scope_dirs}")

    sources = _non_test_py(paths)
    total = len(sources)
    uncovered_dirs: set[str] = set()
    in_scope = 0
    for relpath in sources:
        directory = _directory_of(relpath)
        if _in_scope(directory, scope_dirs):
            in_scope += 1
        else:
            uncovered_dirs.add(directory)

    print(f"non-test .py files in fetch scope: {in_scope}/{total}")
    if uncovered_dirs:
        print(f"uncovered directories ({len(uncovered_dirs)}):")
        for directory in sorted(uncovered_dirs):
            print(f"  - {directory}")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
