import logging
from collections import defaultdict

from profiler.core.module_markers import (
    ENTRY_MARKERS,
    PACKAGE_MARKERS,
    SOURCE_EXTENSIONS,
)

logger = logging.getLogger(__name__)


class ModuleDetector:
    def detect(self, paths: list[str]) -> list[str]:
        dir_files = self._dir_files(paths)
        package_roots = self._drop_ancestors(
            {d for d, files in dir_files.items() if files & PACKAGE_MARKERS}
        )
        entry_dirs = {d for d, files in dir_files.items() if files & ENTRY_MARKERS}
        qualifying = {d for d in entry_dirs if not self._enclosed(d, package_roots)}
        roots = self._drop_ancestors(package_roots | qualifying)
        roots |= self._library_roots(paths, roots)
        ordered = sorted(roots, key=lambda r: (r.count("/"), r))
        logger.info("Detected %d module roots: %s", len(ordered), ordered)
        return ordered

    def _dir_files(self, paths: list[str]) -> dict[str, set[str]]:
        dir_files: dict[str, set[str]] = defaultdict(set)
        for path in paths:
            parts = path.split("/")
            dir_files["/".join(parts[:-1])].add(parts[-1])
        return dir_files

    def _drop_ancestors(self, dirs: set[str]) -> set[str]:
        return {d for d in dirs if not self._has_descendant(d, dirs)}

    def _has_descendant(self, candidate: str, candidates: set[str]) -> bool:
        prefix = candidate + "/" if candidate else ""
        return any(other != candidate and other.startswith(prefix) for other in candidates)

    def _enclosed(self, directory: str, package_roots: set[str]) -> bool:
        return any(
            root == "" or directory == root or directory.startswith(root + "/")
            for root in package_roots
        )

    def _library_roots(self, paths: list[str], roots: set[str]) -> set[str]:
        if "" in roots:
            return set()
        by_top: dict[str, list[str]] = defaultdict(list)
        for path in paths:
            parts = path.split("/")
            if len(parts) > 1:
                by_top[parts[0]].append(path)
        extra = set()
        for top, top_paths in by_top.items():
            if top in roots or any(r.startswith(top + "/") for r in roots):
                continue
            if any(self._is_source(p) for p in top_paths):
                extra.add(top)
        return extra

    def service_roots(self, paths: list[str], roots: list[str]) -> set[str]:
        dir_files = self._dir_files(paths)
        entry_dirs = {d for d, files in dir_files.items() if files & ENTRY_MARKERS}
        result: set[str] = set()
        for root in roots:
            if any(
                d == root or d.startswith(root + "/") or root == ""
                for d in entry_dirs
            ):
                result.add(root)
        return result

    def _is_source(self, path: str) -> bool:
        return any(path.endswith(ext) for ext in SOURCE_EXTENSIONS)
