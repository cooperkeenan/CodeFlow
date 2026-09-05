import json
import logging
import re

import anthropic
from tracer.models.naming import NodeNaming, ReviewFinding, ReviewResult
from tracer.prompts.flow_review_prompt import (
    FLOW_REVIEW_SYSTEM_PROMPT,
    build_review_bundle,
)
from tracer.services.analysis.llm_telemetry import log_llm_call
from tracer.services.analysis.fingerprints import compute_review_fingerprint
from tracer.services.analysis.labelling.name_validator import NameValidator
from tracer.services.analysis.labelling.review_cache import ReviewCache

from shared.models.flow_graph import FlowGraph, FlowNode, Lane

logger = logging.getLogger(__name__)
_MODEL = "claude-haiku-4-5-20251001"


class FlowReviewer:
    def __init__(
        self,
        anthropic_client: anthropic.Anthropic,
        cache: ReviewCache,
        validator: NameValidator,
    ) -> None:
        self._llm = anthropic_client
        self._cache = cache
        self._validator = validator

    def review(self, graph: FlowGraph) -> FlowGraph:
        bundle = build_review_bundle(graph)
        if not bundle:
            return graph
        fingerprint = compute_review_fingerprint(bundle)
        result = self._cache.get(fingerprint)
        if result is None:
            result, cacheable = self._review_bundle(bundle, graph)
            if cacheable:
                self._cache.put(fingerprint, result)
                self._cache.flush()
        return self._apply(graph, result)

    def _review_bundle(self, bundle: list[dict], graph: FlowGraph) -> tuple[ReviewResult, bool]:
        try:
            raw = self._call(bundle)
            return self._validate(raw, graph), True
        except Exception as exc:
            logger.warning("Flow review fell back for bundle of %d: %s", len(bundle), exc)
            return ReviewResult(corrected={}, page_title="", lane_titles={}, findings=[]), False

    def _call(self, bundle: list[dict]) -> dict:
        content = json.dumps({"nodes": bundle})
        response = self._llm.messages.create(
            model=_MODEL,
            max_tokens=4000,
            temperature=0,
            system=FLOW_REVIEW_SYSTEM_PROMPT,
            messages=[{"role": "user", "content": content}],
        )
        log_llm_call("review", len(bundle), FLOW_REVIEW_SYSTEM_PROMPT, content, response)
        text = next((b.text for b in response.content if b.type == "text"), "")
        match = re.search(r"\{.*\}", text, re.DOTALL)
        if not match:
            raise ValueError("LLM did not return valid JSON")
        return json.loads(match.group())

    def _validate(self, raw: dict, graph: FlowGraph) -> ReviewResult:
        corrected = self._validator.validate(raw, graph)
        page_title = self._clean_text(raw.get("page_title"))
        lane_ids = {lane.id for lane in graph.lanes}
        lane_titles = {
            lane_id: self._clean_text(title)
            for lane_id, title in (raw.get("lanes") or {}).items()
            if lane_id in lane_ids and self._clean_text(title)
        }
        node_ids = {node.id for node in graph.nodes}
        findings = sorted(
            (
                ReviewFinding(node_id=item["node_id"], issue=self._clean_text(item.get("issue")))
                for item in (raw.get("findings") or [])
                if isinstance(item, dict)
                and item.get("node_id") in node_ids
                and self._clean_text(item.get("issue"))
            ),
            key=lambda finding: finding.node_id,
        )
        return ReviewResult(
            corrected=corrected, page_title=page_title, lane_titles=lane_titles, findings=findings
        )

    def _clean_text(self, value: object) -> str:
        return value.strip() if isinstance(value, str) else ""

    def _apply(self, graph: FlowGraph, result: ReviewResult) -> FlowGraph:
        nodes = [self._node(node, result.corrected) for node in graph.nodes]
        lanes = [self._lane(lane, result.lane_titles) for lane in graph.lanes]
        meta = dict(graph.meta)
        meta["review_findings"] = [
            {"node_id": finding.node_id, "issue": finding.issue} for finding in result.findings
        ]
        return graph.model_copy(
            update={
                "nodes": nodes,
                "lanes": lanes,
                "page_title": result.page_title or graph.page_title,
                "meta": meta,
            }
        )

    def _node(self, node: FlowNode, corrected: dict[str, NodeNaming]) -> FlowNode:
        naming = corrected.get(node.id)
        if naming is None:
            return node
        return node.model_copy(update={"llm_label": naming.label, "one_liner": naming.one_liner})

    def _lane(self, lane: Lane, titles: dict[str, str]) -> Lane:
        title = titles.get(lane.id)
        if title is None:
            return lane
        return lane.model_copy(update={"llm_title": title})
