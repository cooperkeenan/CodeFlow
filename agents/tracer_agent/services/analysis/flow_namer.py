import json
import logging
import re

import anthropic
from models.node_name_context import NodeNameContext
from models.node_naming import NodeNaming
from prompts.flow_name_prompt import FLOW_NAME_SYSTEM_PROMPT, build_node_evidence
from services.analysis.name_cache import NameCache
from services.analysis.name_fingerprint import compute_fingerprint
from services.analysis.name_validator import NameValidator
from shared.models.flow_graph import FlowGraph, FlowNode

logger = logging.getLogger(__name__)
_MODEL = "claude-haiku-4-5-20251001"
_BATCH_SIZE = 20


class FlowNamer:
    def __init__(
        self,
        anthropic_client: anthropic.Anthropic,
        cache: NameCache,
        validator: NameValidator,
    ) -> None:
        self._llm = anthropic_client
        self._cache = cache
        self._validator = validator

    def name(self, graph: FlowGraph) -> FlowGraph:
        contexts = self._contexts(graph)
        fingerprints = {c.node.id: compute_fingerprint(c) for c in contexts}
        namings: dict[str, NodeNaming] = {}
        groups: dict[str, list[NodeNameContext]] = {}
        for context in contexts:
            fingerprint = fingerprints[context.node.id]
            cached = self._cache.get(fingerprint)
            if cached is not None:
                namings[context.node.id] = cached
            else:
                groups.setdefault(fingerprint, []).append(context)
        representatives = sorted(
            (group[0] for group in groups.values()), key=lambda c: c.node.id
        )
        for start in range(0, len(representatives), _BATCH_SIZE):
            batch = representatives[start : start + _BATCH_SIZE]
            batch_namings = self._name_batch(batch, graph)
            for context in batch:
                fingerprint = fingerprints[context.node.id]
                naming = batch_namings[context.node.id]
                self._cache.put(fingerprint, naming)
                for duplicate in groups[fingerprint]:
                    namings[duplicate.node.id] = naming
        self._cache.flush()
        return self._apply(graph, namings)

    def _name_batch(
        self, batch: list[NodeNameContext], graph: FlowGraph
    ) -> dict[str, NodeNaming]:
        try:
            raw = self._call(batch)
            parsed = self._validator.validate(raw, graph)
        except Exception as exc:
            logger.warning("Flow naming fell back for batch of %d: %s", len(batch), exc)
            parsed = {}
        for context in batch:
            if context.node.id not in parsed:
                parsed[context.node.id] = self._backfill(context.node)
        return parsed

    def _call(self, batch: list[NodeNameContext]) -> dict:
        response = self._llm.messages.create(
            model=_MODEL,
            max_tokens=4000,
            temperature=0,
            system=FLOW_NAME_SYSTEM_PROMPT,
            messages=[{"role": "user", "content": build_node_evidence(batch)}],
        )
        text = next((b.text for b in response.content if b.type == "text"), "")
        match = re.search(r"\{.*\}", text, re.DOTALL)
        if not match:
            raise ValueError("LLM did not return valid JSON")
        return json.loads(match.group())

    def _backfill(self, node: FlowNode) -> NodeNaming:
        return NodeNaming(label=node.label, one_liner=node.label)

    def _contexts(self, graph: FlowGraph) -> list[NodeNameContext]:
        label_by_id = {node.id: node.label for node in graph.nodes}
        arm_sources: dict[str, list[str]] = {}
        for edge in graph.edges:
            if edge.kind == "arm":
                arm_sources.setdefault(edge.source, []).append(edge.arm_label)
        contexts = []
        for node in graph.nodes:
            children = tuple(
                label_by_id[child] for child in node.hidden_children if child in label_by_id
            )
            contexts.append(
                NodeNameContext(
                    node=node,
                    arm_label_sources=tuple(arm_sources.get(node.id, [])),
                    child_labels=children,
                )
            )
        return contexts

    def _apply(self, graph: FlowGraph, namings: dict[str, NodeNaming]) -> FlowGraph:
        return graph.model_copy(
            update={"nodes": [self._node(node, namings) for node in graph.nodes]}
        )

    def _node(self, node: FlowNode, namings: dict[str, NodeNaming]) -> FlowNode:
        naming = namings.get(node.id)
        if naming is None:
            return node
        return node.model_copy(update={"llm_label": naming.label, "one_liner": naming.one_liner})
