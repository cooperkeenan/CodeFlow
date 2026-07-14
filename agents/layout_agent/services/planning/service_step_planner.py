import json
import logging
import re

import anthropic
from core.hierarchy_config import HierarchyConfig
from helpers.service_step_validator import ServiceStepValidator
from models.service_step import ServiceStep, ServiceStepPlan
from prompts.service_step_prompt import SERVICE_STEP_SYSTEM_PROMPT, build_service_evidence
from shared.models.diagram_spec import Component, DiagramSpec, Module

logger = logging.getLogger(__name__)
_MODEL = "claude-haiku-4-5-20251001"


class ServiceStepPlanner:
    def __init__(
        self,
        anthropic_client: anthropic.AsyncAnthropic,
        validator: ServiceStepValidator,
        config: HierarchyConfig,
    ) -> None:
        self._llm = anthropic_client
        self._validator = validator
        self._config = config

    async def plan(self, spec: DiagramSpec, module: Module) -> ServiceStepPlan:
        all_names = {c.name for comps in module.zones.values() for c in comps}
        components: list[Component] = [c for comps in module.zones.values() for c in comps]
        edges = [
            e
            for e in spec.edges
            if e.source in all_names and e.target in all_names and e.source != e.target
        ]
        evidence = build_service_evidence(module, components, edges)
        try:
            raw = await self._call(evidence)
            return self._validator.validate(raw, module)
        except Exception as exc:
            logger.warning("Service step planning fell back for %s: %s", module.name, exc)
            return self._fallback(module)

    async def _call(self, evidence: str) -> dict:
        response = await self._llm.messages.create(
            model=_MODEL,
            max_tokens=4000,
            temperature=0,
            system=SERVICE_STEP_SYSTEM_PROMPT,
            messages=[{"role": "user", "content": evidence}],
        )
        text = next((b.text for b in response.content if b.type == "text"), "")
        match = re.search(r"\{.*\}", text, re.DOTALL)
        if not match:
            raise ValueError("LLM did not return valid JSON")
        return json.loads(match.group())

    def _fallback(self, module: Module) -> ServiceStepPlan:
        primary_comps: list[Component] = []
        for comps in module.zones.values():
            primary_comps.extend(
                c for c in comps if not c.nested and c.tier == "primary"
            )
        capped = primary_comps[: self._config.service_max_steps]
        steps = tuple(
            ServiceStep(
                label=c.name,
                description=c.description or "",
                backing_components=(c.name,),
                order_index=i,
            )
            for i, c in enumerate(capped)
        )
        return ServiceStepPlan(
            module_name=module.name,
            purpose=module.description or "",
            diagram_type="dependency_graph",
            steps=steps,
        )
