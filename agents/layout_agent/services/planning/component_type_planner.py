import json
import logging
import re

import anthropic

from prompts.component_type_prompt import COMPONENT_TYPE_SYSTEM_PROMPT, build_component_evidence
from shared.models.diagram_spec import DiagramSpec
from shared.models.diagram_template import DiagramType

logger = logging.getLogger(__name__)

_MODEL = "claude-haiku-4-5-20251001"
_VALID_TYPES: frozenset[DiagramType] = frozenset(
    {"pipeline", "hub_and_spoke", "hierarchy", "dependency_graph", "relationship"}
)
_HIGH_LEVEL_ROLES = frozenset({"entry", "orchestrator"})


class ComponentTypePlanner:
    def __init__(self, llm: anthropic.AsyncAnthropic) -> None:
        self._llm = llm

    async def plan(self, spec: DiagramSpec, view_set: set[str]) -> dict[str, dict]:
        comp_data = self._gather(spec, view_set)
        if not comp_data:
            return {}
        by_module: dict[str, list[dict]] = {}
        for c in comp_data:
            by_module.setdefault(c["module"], []).append(c)
        result: dict[str, dict] = {}
        for chunk in by_module.values():
            result.update(await self._plan_chunk(chunk))
        fallback_n = len(comp_data) - len(result)
        if fallback_n:
            logger.warning(
                "ComponentTypePlanner: %d/%d components using classifier fallback",
                fallback_n, len(comp_data),
            )
        return result

    async def _plan_chunk(self, chunk: list[dict]) -> dict[str, dict]:
        try:
            raw = await self._call(build_component_evidence(chunk))
            return self._validate(raw, chunk)
        except Exception as exc:
            logger.warning(
                "ComponentTypePlanner: chunk [%s] failed (%s); falling back",
                ", ".join(c["name"] for c in chunk), exc,
            )
            return {}

    def _gather(self, spec: DiagramSpec, view_set: set[str]) -> list[dict]:
        all_comps = {c.name: c for m in spec.modules for cs in m.zones.values() for c in cs}
        comp_to_mod = {c.name: m.name for m in spec.modules for cs in m.zones.values() for c in cs}
        callees_map: dict[str, list[str]] = {}
        callers_map: dict[str, list[str]] = {}
        for e in spec.edges:
            if e.edge_type != "import" and e.source != e.target:
                callees_map.setdefault(e.source, []).append(e.target)
                callers_map.setdefault(e.target, []).append(e.source)
        result = []
        for name in sorted(view_set):
            c = all_comps.get(name)
            if not c:
                continue
            callees = callees_map.get(name, [])
            children = [ch for ch in (c.children or []) if ch in all_comps]
            is_high = len(callees) + len(children) >= 2 or (c.role or "") in _HIGH_LEVEL_ROLES
            if not is_high:
                continue
            result.append({
                "name": name,
                "description": c.description or "",
                "role": c.role or "",
                "module": comp_to_mod.get(name, ""),
                "callers": callers_map.get(name, []),
                "callees": callees,
                "children": children,
            })
        return result

    async def _call(self, evidence: str) -> dict:
        response = await self._llm.messages.create(
            model=_MODEL, max_tokens=8000, temperature=0,
            system=COMPONENT_TYPE_SYSTEM_PROMPT,
            messages=[{"role": "user", "content": evidence}],
        )
        text = next((b.text for b in response.content if b.type == "text"), "")
        match = re.search(r"\{.*\}", text, re.DOTALL)
        if not match:
            raise ValueError("no JSON in response")
        return json.loads(match.group()).get("components", {})

    def _validate(self, raw: dict, comp_data: list[dict]) -> dict[str, dict]:
        valid_names = {c["name"] for c in comp_data}
        result: dict[str, dict] = {}
        for name, entry in raw.items():
            if name not in valid_names or not isinstance(entry, dict):
                continue
            t = entry.get("type")
            if t not in _VALID_TYPES:
                continue
            order = entry.get("order")
            result[name] = {
                "type": t,
                "reasoning": entry.get("reasoning", ""),
                "order": order if isinstance(order, list) else None,
            }
        return result
