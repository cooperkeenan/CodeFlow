from collections import defaultdict
from dataclasses import dataclass

from shared.models.diagram_spec import Component, DiagramSpec


@dataclass(frozen=True)
class ComponentMetrics:
    name: str
    module: str
    zone: str
    description: str
    fan_in: int
    fan_out: int
    child_count: int
    is_entry: bool


class ComponentMetricsBuilder:
    def build(self, spec: DiagramSpec) -> dict[str, ComponentMetrics]:
        fan_out: dict[str, int] = defaultdict(int)
        fan_in: dict[str, int] = defaultdict(int)
        for edge in spec.edges:
            fan_out[edge.source] += 1
            fan_in[edge.target] += 1
        entries = set(spec.entry_points)
        metrics: dict[str, ComponentMetrics] = {}
        for module in spec.modules:
            for zone, components in module.zones.items():
                for component in components:
                    metrics[component.name] = self._for(
                        component, module.name, zone, fan_in, fan_out, entries
                    )
        return metrics

    def _for(
        self,
        component: Component,
        module: str,
        zone: str,
        fan_in: dict[str, int],
        fan_out: dict[str, int],
        entries: set[str],
    ) -> ComponentMetrics:
        return ComponentMetrics(
            name=component.name,
            module=module,
            zone=zone,
            description=component.description,
            fan_in=fan_in.get(component.name, 0),
            fan_out=fan_out.get(component.name, 0),
            child_count=len(component.children),
            is_entry=component.name in entries,
        )
