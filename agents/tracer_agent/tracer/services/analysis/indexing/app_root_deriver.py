import ast

from tracer.models.index_records import ProjectIndex
from tracer.services.analysis.syntax.call_expr_split import call_name


class AppRootDeriver:
    def derive(self, index: ProjectIndex) -> frozenset[str]:
        app_modules = sorted(self._app_modules(index))
        candidates = {
            module: candidate
            for module in app_modules
            for candidate in (self._candidate(module, index.source_roots),)
            if candidate is not None
        }
        counts: dict[str, int] = {}
        for candidate in candidates.values():
            counts[candidate] = counts.get(candidate, 0) + 1
        roots: set[str] = set()
        for module, candidate in candidates.items():
            if counts[candidate] == 1:
                roots.add(candidate)
                continue
            roots.add(self._package(module))
        return frozenset(roots)

    def _app_modules(self, index: ProjectIndex) -> tuple[str, ...]:
        found: list[str] = []
        for module_fqn in index.modules:
            module_record = index.functions.get(f"{module_fqn}.<module>")
            if module_record is None:
                continue
            if self._has_fastapi_assign(module_record.body):
                found.append(module_fqn)
        return tuple(found)

    def _has_fastapi_assign(self, tree: ast.AST) -> bool:
        for stmt in tree.body:
            if not (isinstance(stmt, ast.Assign) and isinstance(stmt.value, ast.Call)):
                continue
            if call_name(stmt.value) == "FastAPI":
                return True
        return False

    def _candidate(self, module: str, source_roots: frozenset[str]) -> str | None:
        matches = [r for r in source_roots if module.startswith(f"{r}.")]
        if matches:
            return max(matches, key=len)
        package = self._package(module)
        return package or None

    def _package(self, module: str) -> str:
        parts = module.split(".")
        return ".".join(parts[:-1])
