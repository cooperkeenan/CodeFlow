import logging
from collections import defaultdict

from helpers.component_metrics import ComponentMetricsBuilder
from shared.models.diagram_spec import Component, DiagramSpec

logger = logging.getLogger(__name__)


class OwnershipResolver:
    def __init__(self, metrics_builder: ComponentMetricsBuilder):
        self._metrics = metrics_builder

    def resolve(self, spec: DiagramSpec) -> None:
        all_comps: dict[str, Component] = {
            c.name: c
            for m in spec.modules
            for comps in m.zones.values()
            for c in comps
        }
        comp_to_module: dict[str, str] = {
            c.name: m.name
            for m in spec.modules
            for comps in m.zones.values()
            for c in comps
        }
        metrics = self._metrics.build(spec)

        owners: dict[str, list[str]] = defaultdict(list)
        for comp in all_comps.values():
            for child_name in comp.children:
                if child_name in all_comps:
                    owners[child_name].append(comp.name)

        for child_name, parent_names in owners.items():
            if self._would_cycle(child_name, parent_names, all_comps):
                logger.warning("Cycle detected: skipping ownership of %s", child_name)
                continue

            child_module = comp_to_module.get(child_name)
            same_module = [p for p in parent_names if comp_to_module.get(p) == child_module]
            candidates = same_module if same_module else parent_names
            canonical = min(
                candidates,
                key=lambda p: (-(metrics[p].fan_out if p in metrics else 0), p),
            )

            for parent_name in parent_names:
                if parent_name != canonical:
                    parent = all_comps.get(parent_name)
                    if parent:
                        parent.children = [c for c in parent.children if c != child_name]

            child_comp = all_comps.get(child_name)
            if child_comp:
                child_comp.nested = True

    def _would_cycle(
        self, child_name: str, parent_names: list[str], all_comps: dict[str, Component]
    ) -> bool:
        visited: set[str] = set()
        queue = list(all_comps[child_name].children) if child_name in all_comps else []
        parent_set = set(parent_names)
        while queue:
            current = queue.pop()
            if current in visited:
                continue
            visited.add(current)
            if current in parent_set:
                return True
            comp = all_comps.get(current)
            if comp:
                queue.extend(comp.children)
        return False
