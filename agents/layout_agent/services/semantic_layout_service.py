import json
import logging
import re

import anthropic
from prompts.semantic_prompt import SEMANTIC_SYSTEM_PROMPT
from helpers.component_metrics import ComponentMetrics, ComponentMetricsBuilder
from helpers.importance_scorer import ImportanceScorer
from helpers.semantic_validator import SemanticAnnotations, SemanticValidator

from shared.models.diagram_spec import DiagramSpec

logger = logging.getLogger(__name__)

_MODEL = "claude-haiku-4-5-20251001"


class SemanticLayoutService:
    def __init__(
        self,
        anthropic_client: anthropic.AsyncAnthropic,
        metrics_builder: ComponentMetricsBuilder,
        scorer: ImportanceScorer,
        validator: SemanticValidator,
    ):
        self._llm = anthropic_client
        self._metrics = metrics_builder
        self._scorer = scorer
        self._validator = validator

    async def enrich(self, spec: DiagramSpec) -> DiagramSpec:
        metrics = self._metrics.build(spec)
        fallback_tiers = self._scorer.primary_tiers(metrics)
        try:
            raw = await self._call(self._evidence(spec, metrics))
            annotations = self._validator.validate(raw, spec, fallback_tiers)
            logger.info("Semantic enrichment: LLM annotations applied")
        except Exception as exc:
            logger.warning("Semantic enrichment fell back to deterministic tiers: %s", exc)
            annotations = SemanticAnnotations(component_tiers=fallback_tiers)
        self._merge(spec, annotations)
        return spec

    def _evidence(self, spec: DiagramSpec, metrics: dict[str, ComponentMetrics]) -> str:
        modules = [{"name": m.name, "zones": list(m.zones.keys())} for m in spec.modules]
        components = [
            {
                "name": metric.name,
                "module": metric.module,
                "zone": metric.zone,
                "description": metric.description,
                "fan_in": metric.fan_in,
                "fan_out": metric.fan_out,
                "child_count": metric.child_count,
                "is_entry": metric.is_entry,
            }
            for metric in metrics.values()
        ]
        return json.dumps({"modules": modules, "components": components})

    async def _call(self, evidence: str) -> dict:
        response = await self._llm.messages.create(
            model=_MODEL,
            max_tokens=6000,
            temperature=0,
            system=SEMANTIC_SYSTEM_PROMPT,
            messages=[{"role": "user", "content": evidence}],
        )
        text = next((b.text for b in response.content if b.type == "text"), "")
        logger.info("semantic_layout raw output: %s", text)
        match = re.search(r"\{.*\}", text, re.DOTALL)
        if not match:
            raise ValueError("LLM did not return valid JSON")
        return json.loads(match.group())

    def _merge(self, spec: DiagramSpec, annotations: SemanticAnnotations) -> None:
        for module in spec.modules:
            module.purpose = annotations.module_purposes.get(module.name, module.purpose)
            for components in module.zones.values():
                for component in components:
                    component.tier = annotations.component_tiers.get(component.name, "primary")
                    component.role = annotations.component_roles.get(component.name, component.role)
        for edge in spec.edges:
            edge.primary = self._edge_primary(edge.source, edge.target, annotations)

    def _edge_primary(self, source: str, target: str, annotations: SemanticAnnotations) -> bool:
        tiers = annotations.component_tiers
        both_primary = tiers.get(source) == "primary" and tiers.get(target) == "primary"
        if not both_primary or not annotations.primary_edges:
            return True
        return (source, target) in annotations.primary_edges
