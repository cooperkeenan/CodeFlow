import json
import logging
import re

import anthropic
from helpers.flow_label_validator import FlowLabelValidator
from models.flow_label_maps import FlowLabelMaps
from prompts.flow_label_prompt import FLOW_LABEL_SYSTEM_PROMPT, arm_key_map, build_flow_evidence
from shared.models.flow_graph import FlowEdge, FlowGraph, FlowNode, Lane

logger = logging.getLogger(__name__)
_MODEL = "claude-haiku-4-5-20251001"


class FlowLabeler:
    def __init__(
        self,
        anthropic_client: anthropic.AsyncAnthropic,
        validator: FlowLabelValidator,
    ) -> None:
        self._llm = anthropic_client
        self._validator = validator

    async def label(self, graph: FlowGraph) -> FlowGraph:
        try:
            raw = await self._call(build_flow_evidence(graph))
            maps = self._validator.validate(raw, graph)
        except Exception as exc:
            logger.warning("Flow labeling fell back for %s: %s", graph.repo, exc)
            return graph
        return self._apply(graph, maps)

    async def _call(self, evidence: str) -> dict:
        response = await self._llm.messages.create(
            model=_MODEL,
            max_tokens=4000,
            temperature=0,
            system=FLOW_LABEL_SYSTEM_PROMPT,
            messages=[{"role": "user", "content": evidence}],
        )
        text = next((b.text for b in response.content if b.type == "text"), "")
        match = re.search(r"\{.*\}", text, re.DOTALL)
        if not match:
            raise ValueError("LLM did not return valid JSON")
        return json.loads(match.group())

    def _apply(self, graph: FlowGraph, maps: FlowLabelMaps) -> FlowGraph:
        arm_edge_keys = {id(edge): key for key, edge in arm_key_map(graph).items()}
        return FlowGraph(
            repo=graph.repo,
            page_title=maps.page_title or graph.page_title,
            lanes=[self._lane(lane, maps) for lane in graph.lanes],
            nodes=[self._node(node, maps) for node in graph.nodes],
            edges=[self._edge(edge, maps, arm_edge_keys) for edge in graph.edges],
            meta=graph.meta,
        )

    def _lane(self, lane: Lane, maps: FlowLabelMaps) -> Lane:
        return lane.model_copy(update={"llm_title": maps.lane_titles.get(lane.id)})

    def _node(self, node: FlowNode, maps: FlowLabelMaps) -> FlowNode:
        return node.model_copy(
            update={
                "llm_label": maps.node_labels.get(node.id),
                "one_liner": maps.node_one_liners.get(node.id, node.one_liner),
            }
        )

    def _edge(
        self, edge: FlowEdge, maps: FlowLabelMaps, arm_edge_keys: dict[int, str]
    ) -> FlowEdge:
        key = arm_edge_keys.get(id(edge))
        llm_label = maps.arm_labels.get(key) if key is not None else None
        return edge.model_copy(update={"llm_label": llm_label})
