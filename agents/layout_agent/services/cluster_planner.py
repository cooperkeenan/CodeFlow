import json
import logging
import re

import anthropic
from prompts.cluster_prompt import CLUSTER_SYSTEM_PROMPT
from helpers.cluster_fallback import ClusterFallback
from helpers.cluster_validator import ClusterValidator
from helpers.component_metrics import ComponentMetrics, ComponentMetricsBuilder

from shared.models.diagram_spec import Component, DiagramSpec, Module, ZoneClusterPlan

logger = logging.getLogger(__name__)

_MODEL = "claude-haiku-4-5-20251001"


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

    async def plan(self, spec: DiagramSpec) -> DiagramSpec:
        metrics = self._metrics.build(spec)
        for module in spec.modules:
            module.cluster_plan = await self._plan_module(spec, module, metrics)
        return spec

    async def _plan_module(
        self, spec: DiagramSpec, module: Module, metrics: dict[str, ComponentMetrics]
    ) -> list[ZoneClusterPlan]:
        if not any(not c.nested for comps in module.zones.values() for c in comps):
            return []
        try:
            raw = await self._call(self._evidence(spec, module, metrics))
            return self._validator.validate(raw, module)
        except Exception as exc:
            logger.warning("Cluster planning fell back for %s: %s", module.name, exc)
            return self._fallback.group_by_role(module)

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
            "name": component.name,
            "role": component.role,
            "tier": component.tier,
            "description": component.description,
            "fan_in": metric.fan_in if metric else 0,
            "fan_out": metric.fan_out if metric else 0,
        }

    async def _call(self, evidence: str) -> dict:
        response = await self._llm.messages.create(
            model=_MODEL,
            max_tokens=4000,
            temperature=0,
            system=CLUSTER_SYSTEM_PROMPT,
            messages=[{"role": "user", "content": evidence}],
        )
        text = next((b.text for b in response.content if b.type == "text"), "")
        logger.debug("cluster_planner raw output: %s", text)
        match = re.search(r"\{.*\}", text, re.DOTALL)
        if not match:
            raise ValueError("LLM did not return valid JSON")
        return json.loads(match.group())
