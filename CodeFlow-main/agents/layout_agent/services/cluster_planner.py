import json
import logging
import re
from collections import Counter
from dataclasses import dataclass

import anthropic
from helpers.cluster_fallback import ClusterFallback
from helpers.cluster_validator import ClusterValidator
from helpers.component_metrics import ComponentMetrics, ComponentMetricsBuilder
from prompts.cluster_prompt import CLUSTER_SYSTEM_PROMPT

from shared.models.diagram_spec import Component, DiagramSpec, Module, ZoneClusterPlan

logger = logging.getLogger(__name__)

_MODEL = "claude-haiku-4-5-20251001"
_STYLE_TO_TYPE = {"pipeline": "pipeline", "hub": "hub_and_spoke", "hierarchy": "hierarchy"}
_VALID_TYPES = {"zoned", "pipeline", "hub_and_spoke", "layered_tier", "hierarchy", "mesh", "dependency_graph"}


@dataclass
class PlanResult:
    spec: DiagramSpec
    module_types: dict[str, str]
    module_rationales: dict[str, str]


class ClusterPlanner:
    def __init__(
        self,
        anthropic_client: anthropic.AsyncAnthropic,
        metrics_builder: ComponentMetricsBuilder,
        validator: ClusterValidator,
        fallback: ClusterFallback,
    ):
        self._llm = anthropic_client
        self._metrics = metrics_builder
        self._validator = validator
        self._fallback = fallback

    async def plan(self, spec: DiagramSpec) -> PlanResult:
        metrics = self._metrics.build(spec)
        module_types: dict[str, str] = {}
        module_rationales: dict[str, str] = {}
        for module in spec.modules:
            plans, diagram_type, rationale = await self._plan_module(spec, module, metrics)
            module.cluster_plan = plans
            module_types[module.name] = diagram_type
            module_rationales[module.name] = rationale
        return PlanResult(spec=spec, module_types=module_types, module_rationales=module_rationales)

    async def _plan_module(
        self, spec: DiagramSpec, module: Module, metrics: dict[str, ComponentMetrics]
    ) -> tuple[list[ZoneClusterPlan], str, str]:
        if not any(not c.nested for comps in module.zones.values() for c in comps):
            return [], "dependency_graph", ""
        try:
            raw = await self._call(self._evidence(spec, module, metrics))
            plans = self._validator.validate(raw, module)
            diagram_type = self._parse_type(raw.get("diagram_type"), plans)
            rationale = raw.get("reasoning", "")
            return plans, diagram_type, rationale
        except Exception as exc:
            logger.warning("Cluster planning fell back for %s: %s", module.name, exc)
            plans = self._fallback.group_by_role(module)
            return plans, self._derive_type(plans), ""

    def _parse_type(self, raw_type: object, plans: list[ZoneClusterPlan]) -> str:
        if isinstance(raw_type, str) and raw_type in _VALID_TYPES:
            return raw_type
        return self._derive_type(plans)

    def _derive_type(self, plans: list[ZoneClusterPlan]) -> str:
        counts: Counter = Counter()
        for zcp in plans:
            for c in zcp.clusters:
                counts[c.style] += 1
        if not counts:
            return "dependency_graph"
        return _STYLE_TO_TYPE.get(counts.most_common(1)[0][0], "dependency_graph")

    def _evidence(
        self, spec: DiagramSpec, module: Module, metrics: dict[str, ComponentMetrics]
    ) -> str:
        names = {c.name for comps in module.zones.values() for c in comps if not c.nested}
        zones = [
            {"zone": zone, "components": [self._component(c, metrics) for c in comps if not c.nested]}
            for zone, comps in module.zones.items()
            if any(c for c in comps if not c.nested)
        ]
        edges = [
            {"source": e.source, "target": e.target, "edge_type": e.edge_type}
            for e in spec.edges
            if e.source in names and e.target in names and e.source != e.target
        ]
        return json.dumps({"module": module.name, "zones": zones, "edges": edges})

    def _component(self, component: Component, metrics: dict[str, ComponentMetrics]) -> dict:
        metric = metrics.get(component.name)
        return {
            "name": component.name, "role": component.role, "tier": component.tier,
            "description": component.description,
            "fan_in": metric.fan_in if metric else 0,
            "fan_out": metric.fan_out if metric else 0,
        }

    async def _call(self, evidence: str) -> dict:
        response = await self._llm.messages.create(
            model=_MODEL, max_tokens=4000, temperature=0,
            system=CLUSTER_SYSTEM_PROMPT,
            messages=[{"role": "user", "content": evidence}],
        )
        text = next((b.text for b in response.content if b.type == "text"), "")
        match = re.search(r"\{.*\}", text, re.DOTALL)
        if not match:
            raise ValueError("LLM did not return valid JSON")
        return json.loads(match.group())
