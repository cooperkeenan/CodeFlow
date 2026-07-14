from core.hierarchy_config import HierarchyConfig
from models.service_step import ServiceStep, ServiceStepPlan
from shared.models.diagram_spec import Module
from shared.models.diagram_template import DiagramType

_ALLOWED_TYPES: frozenset[str] = frozenset(
    {"pipeline", "hub_and_spoke", "hierarchy", "dependency_graph"}
)
_DEFAULT_TYPE: DiagramType = "dependency_graph"


class ServiceStepValidator:
    def __init__(self, config: HierarchyConfig) -> None:
        self._config = config

    def validate(self, raw: dict, module: Module) -> ServiceStepPlan:
        purpose = raw.get("purpose") or ""
        if not isinstance(purpose, str):
            purpose = ""

        raw_type = raw.get("diagram_type")
        diagram_type: DiagramType = (
            raw_type
            if isinstance(raw_type, str) and raw_type in _ALLOWED_TYPES
            else _DEFAULT_TYPE
        )

        all_names = {c.name for comps in module.zones.values() for c in comps}
        primary_names = {
            c.name
            for comps in module.zones.values()
            for c in comps
            if not c.nested and c.tier == "primary"
        }

        raw_steps = raw.get("steps") or []
        steps = self._parse_steps(raw_steps, all_names)
        steps = self._cap_with_preference(steps, primary_names)

        reindexed = tuple(
            ServiceStep(
                label=s.label,
                description=s.description,
                backing_components=s.backing_components,
                order_index=i,
            )
            for i, s in enumerate(steps)
        )

        return ServiceStepPlan(
            module_name=module.name,
            purpose=purpose,
            diagram_type=diagram_type,
            steps=reindexed,
        )

    def _parse_steps(self, raw_steps: list, all_names: set[str]) -> list[ServiceStep]:
        steps: list[ServiceStep] = []
        for entry in raw_steps:
            if not isinstance(entry, dict):
                continue
            raw_comps = entry.get("backing_components") or []
            valid_comps = tuple(n for n in raw_comps if n in all_names)
            if not valid_comps:
                continue
            order_index = int(entry.get("order_index") or 0)
            label = str(entry.get("label") or "Step")
            description = str(entry.get("description") or "")
            steps.append(
                ServiceStep(
                    label=label,
                    description=description,
                    backing_components=valid_comps,
                    order_index=order_index,
                )
            )
        steps.sort(key=lambda s: s.order_index)
        return steps

    def _cap_with_preference(
        self, steps: list[ServiceStep], primary_names: set[str]
    ) -> list[ServiceStep]:
        cap = self._config.service_max_steps
        if len(steps) <= cap:
            return steps
        primary = [
            s for s in steps if any(n in primary_names for n in s.backing_components)
        ]
        other = [
            s for s in steps if not any(n in primary_names for n in s.backing_components)
        ]
        kept = (primary + other)[:cap]
        kept.sort(key=lambda s: s.order_index)
        return kept
