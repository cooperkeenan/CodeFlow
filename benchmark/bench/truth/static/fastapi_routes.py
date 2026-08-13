import ast
from collections.abc import Mapping

from bench.truth.models import STATIC_CONFIDENCE, RouteFact
from bench.truth.normalize import RouteNormalizer
from bench.truth.static.fastapi_scan import UNRESOLVED, ModuleFacts, ModuleScanner
from bench.truth.static.py_files import SourceTree

Key = tuple[str, str]

PROV_OK = "static:ast"
PROV_DYNAMIC_PREFIX = "static:ast-unresolved-prefix"
PROV_NOT_MOUNTED = "static:ast-router-not-mounted"


class FastApiRouteExtractor:
    """Independent AST extraction of FastAPI routes, including prefix resolution.

    Where a prefix is a runtime value (``prefix=settings.API_V1_STR``) it cannot be
    resolved from source at all. Those routes are still emitted, flagged, and
    counted in the notes rather than silently dropped or silently wrong.
    """

    def __init__(self, normalizer: RouteNormalizer) -> None:
        self._normalizer = normalizer

    def extract(self, tree: SourceTree) -> tuple[list[RouteFact], list[str]]:
        modules, unparsed = self._scan(tree)
        prefixes = self._resolve_prefixes(modules)
        facts, notes = self._emit(modules, prefixes)
        if unparsed:
            listed = ", ".join(unparsed[:5])
            notes.append(
                f"{len(unparsed)} file(s) could not be parsed and were skipped ({listed}). "
                "Any routes they declare are missing from this ground truth."
            )
        return facts, notes

    def _scan(self, tree: SourceTree) -> tuple[dict[str, ModuleFacts], list[str]]:
        modules: dict[str, ModuleFacts] = {}
        unparsed: list[str] = []
        for relative, text in tree.sources.items():
            module = tree.modules.get(relative, "")
            try:
                parsed = ast.parse(text)
            except SyntaxError:
                unparsed.append(relative)
                continue
            scanner = ModuleScanner(module)
            scanner.visit(parsed)
            facts = scanner.facts
            if facts.routes or facts.routers or facts.includes:
                modules[module] = facts
        return modules, sorted(unparsed)

    def _resolve_target(self, facts: ModuleFacts, target: str) -> Key | None:
        if "." not in target and target in facts.routers:
            return (facts.module, target)
        head, _, rest = target.partition(".")
        base = facts.imports.get(head)
        if base is None:
            return (facts.module, target) if not rest else None
        full = f"{base}.{rest}" if rest else base
        module, _, var = full.rpartition(".")
        return (module, var) if module else None

    def _own_prefix(self, modules: Mapping[str, ModuleFacts], key: Key) -> str:
        facts = modules.get(key[0])
        return facts.routers.get(key[1], "") if facts else ""

    def _resolve_prefixes(self, modules: Mapping[str, ModuleFacts]) -> dict[Key, set[str]]:
        edges: list[tuple[Key, Key, str]] = []
        for facts in modules.values():
            for include in facts.includes:
                parent = self._resolve_target(facts, include.parent_var)
                child = self._resolve_target(facts, include.target)
                if parent and child:
                    edges.append((parent, child, include.prefix))

        prefixes: dict[Key, set[str]] = {}
        for module, facts in modules.items():
            for app_var in facts.apps:
                prefixes[(module, app_var)] = {""}

        for _ in range(len(edges) + 1):
            changed = False
            for parent, child, include_prefix in edges:
                for parent_prefix in sorted(prefixes.get(parent, set())):
                    combined = parent_prefix + include_prefix + self._own_prefix(modules, child)
                    if combined not in prefixes.setdefault(child, set()):
                        prefixes[child].add(combined)
                        changed = True
            if not changed:
                break
        return prefixes

    def _emit(
        self, modules: Mapping[str, ModuleFacts], prefixes: Mapping[Key, set[str]]
    ) -> tuple[list[RouteFact], list[str]]:
        facts: list[RouteFact] = []
        dynamic = 0
        unmounted: set[str] = set()

        for module, module_facts in sorted(modules.items()):
            for route in module_facts.routes:
                key = (module, route.router_var)
                effective = prefixes.get(key)
                if effective is None:
                    unmounted.add(f"{module}:{route.router_var}")
                    effective = {self._own_prefix(modules, key)}
                    provenance = PROV_NOT_MOUNTED
                else:
                    provenance = PROV_OK

                for prefix in sorted(effective):
                    marker = UNRESOLVED in prefix
                    resolved = prefix.replace(UNRESOLVED, "")
                    current = PROV_DYNAMIC_PREFIX if marker else provenance
                    dynamic += bool(marker)
                    for method in route.methods:
                        facts.append(
                            RouteFact(
                                canonical=self._normalizer.canonical(method, resolved + route.path),
                                handler=route.handler,
                                provenance=current,
                                confidence=0.5 if current != PROV_OK else STATIC_CONFIDENCE,
                            )
                        )

        notes: list[str] = []
        if dynamic:
            notes.append(
                f"{dynamic} route(s) sit behind a non-literal prefix (e.g. "
                "prefix=settings.API_V1_STR). Static analysis cannot resolve these; "
                "their paths are missing that segment. Runtime introspection resolves them."
            )
        if unmounted:
            listed = ", ".join(sorted(unmounted)[:5])
            notes.append(
                f"{len(unmounted)} router(s) had no resolvable include chain to an app "
                f"({listed}). Their routes are emitted with their own prefix only."
            )
        return facts, notes
