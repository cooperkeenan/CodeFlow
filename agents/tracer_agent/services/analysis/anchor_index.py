from collections import defaultdict

from models.call_site import CallSite
from models.dispatch_site import DispatchSite
from models.effect_site import EffectSite
from models.parallel_site import ParallelSite
from models.project_index import ProjectIndex
from models.significance_result import SignificanceResult
from services.analysis.component_index import ComponentIndex


class AnchorIndex:
    def __init__(
        self,
        index: ProjectIndex,
        components: ComponentIndex,
        significance: SignificanceResult,
        callsites: tuple[CallSite, ...],
        dispatch_sites: tuple[DispatchSite, ...],
        effects: tuple[EffectSite, ...],
        parallel_sites: tuple[ParallelSite, ...],
    ) -> None:
        self._index = index
        self._components = components
        self._significance = significance
        self._calls: dict[str, list[CallSite]] = defaultdict(list)
        for site in callsites:
            self._calls[site.caller].append(site)
        self._dispatch: dict[str, list[DispatchSite]] = defaultdict(list)
        for site in dispatch_sites:
            self._dispatch[site.owner].append(site)
        self._func_effects: dict[str, list[EffectSite]] = defaultdict(list)
        self._class_effects: dict[str, list[EffectSite]] = defaultdict(list)
        for effect in effects:
            if effect.owner in index.classes:
                self._class_effects[effect.owner].append(effect)
            else:
                self._func_effects[effect.owner].append(effect)
        self._parallel: dict[str, list[ParallelSite]] = defaultdict(list)
        for site in parallel_sites:
            self._parallel[site.owner].append(site)

    def verdict_of(self, site_id: str) -> str | None:
        verdict = self._significance.verdicts.get(site_id)
        return verdict.verdict if verdict is not None else None

    def calls_of(self, fqn: str) -> tuple[CallSite, ...]:
        return tuple(sorted(self._calls.get(fqn, ()), key=lambda c: (c.line, c.call_source)))

    def dispatches_of(self, fqn: str) -> tuple[DispatchSite, ...]:
        return tuple(self._dispatch.get(fqn, ()))

    def func_effects_of(self, fqn: str) -> tuple[EffectSite, ...]:
        return tuple(self._func_effects.get(fqn, ()))

    def parallels_of(self, fqn: str) -> tuple[ParallelSite, ...]:
        return tuple(self._parallel.get(fqn, ()))

    def is_project_function(self, fqn: str) -> bool:
        return fqn in self._index.functions

    def boundary_effects(self, target_fqn: str) -> tuple[EffectSite, ...]:
        classes = self._target_classes(target_fqn)
        seen: dict[str, EffectSite] = {}
        for class_fqn in classes:
            for effect in self._class_effects.get(class_fqn, ()):
                seen[effect.id] = effect
        return tuple(sorted(seen.values(), key=lambda e: e.id))

    def _target_classes(self, target_fqn: str) -> list[str]:
        owner = self._components.component_of(target_fqn)
        classes: list[str] = []
        if owner is not None:
            classes.append(owner)
            classes.extend(self._index.implementations(owner))
        return classes
