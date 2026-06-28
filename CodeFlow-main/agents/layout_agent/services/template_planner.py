import json
import logging

import anthropic

from prompts.template_prompt import TEMPLATE_SYSTEM_PROMPT, build_evidence
from shared.models.diagram_spec import DiagramSpec
from shared.models.diagram_template import DiagramTemplate
from templates.registry import TemplateRegistry
from tools.select_diagram_template_tool import SELECT_DIAGRAM_TEMPLATE_SCHEMA, SelectDiagramTemplateTool

logger = logging.getLogger(__name__)

_MODEL = "claude-haiku-4-5-20251001"
_MAX_RETRIES = 2


class TemplatePlanner:
    def __init__(
        self,
        llm: anthropic.AsyncAnthropic,
        tool: SelectDiagramTemplateTool,
        registry: TemplateRegistry,
    ) -> None:
        self._llm = llm
        self._tool = tool
        self._registry = registry

    async def plan(self, spec: DiagramSpec) -> DiagramTemplate:
        self._tool.bind_spec(spec)
        evidence = build_evidence(spec, self._registry)
        logger.info("TemplatePlanner: modules=%d", len(spec.modules))
        try:
            template = await self._loop(evidence)
        except Exception as exc:
            logger.warning("TemplatePlanner: loop failed (%s); using mesh fallback", exc)
            template = await self._mesh_fallback()
        logger.info("TemplatePlanner: chosen type=%s nodes=%d", template.type, len(template.nodes))
        return template

    async def _loop(self, evidence: str) -> DiagramTemplate:
        messages: list[dict] = [{"role": "user", "content": evidence}]
        retries = 0
        while retries <= _MAX_RETRIES:
            response = await self._llm.messages.create(
                model=_MODEL,
                max_tokens=1024,
                temperature=0,
                system=TEMPLATE_SYSTEM_PROMPT,
                messages=messages,
                tools=[SELECT_DIAGRAM_TEMPLATE_SCHEMA],
            )
            messages.append({"role": "assistant", "content": response.content})
            tool_block = next((b for b in response.content if b.type == "tool_use"), None)
            if tool_block is None:
                logger.warning("TemplatePlanner: LLM did not call tool; using mesh fallback")
                return await self._mesh_fallback()
            attempted: str = tool_block.input.get("diagram_type", "unknown")
            reasoning: str = tool_block.input.get("reasoning", "")
            result_str = await self._tool.handle(tool_block.input)
            result = json.loads(result_str)
            messages.append({
                "role": "user",
                "content": [{"type": "tool_result", "tool_use_id": tool_block.id, "content": result_str}],
            })
            if "limit_hit" not in result and "error" not in result:
                logger.info(
                    "TemplatePlanner: selected %s on attempt %d rationale=%s",
                    attempted, retries + 1, reasoning,
                )
                template = DiagramTemplate.model_validate(result)
                return template.model_copy(update={"meta": {**template.meta, "rationale": reasoning}})
            logger.info(
                "TemplatePlanner: %s rejected limit=%s actual=%s suggested=%s retry=%d",
                attempted, result.get("limit_hit"), result.get("actual_count"),
                result.get("suggested_type"), retries,
            )
            retries += 1
        logger.info("TemplatePlanner: retries exhausted; using mesh fallback")
        return await self._mesh_fallback()

    async def _mesh_fallback(self) -> DiagramTemplate:
        logger.info("TemplatePlanner: deterministic mesh fallback")
        result_str = await self._tool.handle({"diagram_type": "mesh"})
        result = json.loads(result_str)
        if "error" in result:
            raise RuntimeError(f"Mesh fallback failed: {result['error']}")
        return DiagramTemplate.model_validate(result)
