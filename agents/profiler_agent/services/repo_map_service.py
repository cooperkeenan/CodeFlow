import logging
from collections.abc import Iterable

from models.repo_skeleton import DirGroup, ModuleSkeleton, RepoSkeleton
from services.module_detector import ModuleDetector

from core.module_markers import SOURCE_EXTENSIONS

logger = logging.getLogger(__name__)

_MAX_SAMPLES = 6


class RepoMapService:
    def __init__(self, module_detector: ModuleDetector):
        self._detector = module_detector

    def build(self, paths: list[str], repo_name: str) -> RepoSkeleton:
        roots = self._detector.detect(paths)
        services = self._detector.service_roots(paths, roots)
        source_dirs = self._source_dirs(paths)
        owner = self._assign(source_dirs.keys(), roots)
        modules = []
        for root in roots:
            owned = sorted(d for d, r in owner.items() if r == root)
            groups = [
                DirGroup(
                    path=self._as_dir(d),
                    file_count=len(source_dirs[d]),
                    sample_files=sorted(source_dirs[d])[:_MAX_SAMPLES],
                )
                for d in owned
            ]
            if groups:
                modules.append(ModuleSkeleton(
                    name=self._name(root, repo_name),
                    root_path=self._as_dir(root),
                    directories=groups,
                    is_service=(root in services),
                ))
        logger.info("Repo skeleton: %d modules", len(modules))
        return RepoSkeleton(modules=modules)

    def _source_dirs(self, paths: list[str]) -> dict[str, list[str]]:
        dirs: dict[str, list[str]] = {}
        for path in paths:
            if not any(path.endswith(ext) for ext in SOURCE_EXTENSIONS):
                continue
            parts = path.split("/")
            dirs.setdefault("/".join(parts[:-1]), []).append(parts[-1])
        return dirs

    def _assign(self, dirs: Iterable[str], roots: list[str]) -> dict[str, str]:
        owner: dict[str, str] = {}
        for directory in dirs:
            best: str | None = None
            for root in roots:
                if root == "" or directory == root or directory.startswith(root + "/"):
                    if best is None or len(root) > len(best):
                        best = root
            if best is not None:
                owner[directory] = best
        return owner

    def _as_dir(self, path: str) -> str:
        return f"{path}/" if path else ""

    def _name(self, root: str, repo_name: str) -> str:
        if not root:
            return repo_name.split("/")[-1] or "app"
        return root.split("/")[-1]
