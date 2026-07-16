from collections.abc import Mapping

from models.call_site import CallSite
from models.effect_site import EffectSite
from models.project_index import ProjectIndex
from services.analysis.callsite_caller_index import CallSiteCallerIndex
from services.analysis.effect_matcher import CallEffectMatcher
from services.analysis.effect_module_constants import module_string_constants
from services.analysis.effect_route_handler import RouteHandlerInspector
from services.analysis.effect_store_surfacer import StoreEffectSurfacer
from services.analysis.effect_visitor import EffectVisitor


class EffectDetector:
    def __init__(
        self,
        matcher: CallEffectMatcher,
        route_inspector: RouteHandlerInspector,
        store_surfacer: StoreEffectSurfacer,
    ) -> None:
        self._matcher = matcher
        self._route_inspector = route_inspector
        self._store_surfacer = store_surfacer

    def detect(self, index: ProjectIndex, callsites: tuple[CallSite, ...]) -> tuple[EffectSite, ...]:
        caller_index = CallSiteCallerIndex(callsites)
        constants_cache: dict[str, Mapping[str, str]] = {}
        effects: list[EffectSite] = []
        for record in index.functions.values():
            ext_roots = self._ext_roots_by_line(caller_index.callsites_for(record.fqn))
            constants = self._constants(record.module, index, constants_cache)
            bindings = index.modules[record.module].bindings if record.module in index.modules else {}
            response_target = self._route_inspector.inspect(record, bindings)
            visitor = EffectVisitor(record.fqn, ext_roots, self._matcher, constants, response_target)
            visitor.visit(record.body)
            effects.extend(visitor.effects)
        surfaced = self._store_surfacer.surface(effects, index, callsites)
        return tuple(sorted(surfaced, key=lambda effect: effect.id))

    def _ext_roots_by_line(self, sites: tuple[CallSite, ...]) -> dict[int, frozenset[str]]:
        raw: dict[int, set[str]] = {}
        for site in sites:
            for target in site.targets:
                if not target.fqn.startswith("ext:"):
                    continue
                root = target.fqn[4:].split(".")[0]
                if root:
                    raw.setdefault(site.line, set()).add(root)
        return {line: frozenset(roots) for line, roots in raw.items()}

    def _constants(
        self, module: str, index: ProjectIndex, cache: dict[str, Mapping[str, str]]
    ) -> Mapping[str, str]:
        if module not in cache:
            record = index.functions.get(f"{module}.<module>")
            cache[module] = module_string_constants(record.body) if record is not None else {}
        return cache[module]
