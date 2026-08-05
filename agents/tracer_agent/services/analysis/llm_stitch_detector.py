import json
import logging
import re

import anthropic
from models.effect_site import EffectSite
from models.flow_entry import FlowEntry
from models.stitch_verdict import StitchVerdict
from prompts.stitch_judge_prompt import STITCH_JUDGE_SYSTEM_PROMPT, build_stitch_evidence
from services.analysis.path_normalizer import normalize_out_path
from services.analysis.route_matcher import RouteMatcher
from services.analysis.route_stitch_index import RouteStitchIndex
from services.analysis.stitch_fingerprint import compute_stitch_fingerprint
from services.analysis.stitch_verdict_cache import StitchVerdictCache
from shared.models.flow_graph import FlowEdge

logger = logging.getLogger(__name__)
_MODEL = "claude-haiku-4-5-20251001"
_BATCH_SIZE = 20


class LlmStitchDetector:
    def __init__(self, anthropic_client: anthropic.Anthropic, cache: StitchVerdictCache) -> None:
        self._llm = anthropic_client
        self._cache = cache

    def detect(
        self, effects: tuple[EffectSite, ...], entries: tuple[FlowEntry, ...]
    ) -> tuple[FlowEdge, ...]:
        candidates = self._candidates(effects, entries)
        if not candidates:
            return ()
        entry_ids = {entry.id for entry in entries}
        fingerprints = {c.id: compute_stitch_fingerprint(c, entries) for c in candidates}
        results: dict[str, StitchVerdict] = {}
        groups: dict[str, list[EffectSite]] = {}
        for candidate in candidates:
            fingerprint = fingerprints[candidate.id]
            cached = self._cache.get(fingerprint)
            if cached is not None:
                results[candidate.id] = cached
            else:
                groups.setdefault(fingerprint, []).append(candidate)
        representatives = sorted((group[0] for group in groups.values()), key=lambda c: c.id)
        for start in range(0, len(representatives), _BATCH_SIZE):
            batch = representatives[start : start + _BATCH_SIZE]
            batch_verdicts = self._judge_batch(batch, entries, entry_ids)
            for candidate in batch:
                fingerprint = fingerprints[candidate.id]
                verdict = batch_verdicts.get(candidate.id, StitchVerdict(None, 0.0))
                self._cache.put(fingerprint, verdict)
                for duplicate in groups[fingerprint]:
                    results[duplicate.id] = verdict
        self._cache.flush()
        return self._edges(candidates, results, entry_ids)

    def _candidates(
        self, effects: tuple[EffectSite, ...], entries: tuple[FlowEntry, ...]
    ) -> tuple[EffectSite, ...]:
        index = RouteStitchIndex(entries)
        matcher = RouteMatcher()
        unresolved: list[EffectSite] = []
        for effect in effects:
            if effect.kind != "http_out":
                continue
            segments = normalize_out_path(effect.target)
            if segments is not None and matcher.match(effect.method, segments, index) is not None:
                continue
            unresolved.append(effect)
        return tuple(unresolved)

    def _judge_batch(
        self, batch: list[EffectSite], entries: tuple[FlowEntry, ...], entry_ids: set[str]
    ) -> dict[str, StitchVerdict]:
        try:
            payload = self._call(batch, entries)
        except Exception as exc:
            logger.warning("Stitch judging skipped a batch of %d: %s", len(batch), exc)
            return {}
        by_id = {c.id for c in batch}
        verdicts: dict[str, StitchVerdict] = {}
        for entry in payload:
            call_id = entry.get("id")
            verdict = self._parse_verdict(entry, entry_ids)
            if verdict is None or call_id not in by_id:
                continue
            verdicts[call_id] = verdict
        return verdicts

    def _call(self, batch: list[EffectSite], entries: tuple[FlowEntry, ...]) -> list[dict]:
        response = self._llm.messages.create(
            model=_MODEL,
            max_tokens=4000,
            temperature=0,
            system=STITCH_JUDGE_SYSTEM_PROMPT,
            messages=[{"role": "user", "content": build_stitch_evidence(tuple(batch), entries)}],
        )
        text = next((b.text for b in response.content if b.type == "text"), "")
        match = re.search(r"\{.*\}", text, re.DOTALL)
        if not match:
            raise ValueError("LLM did not return valid JSON")
        payload = json.loads(match.group())
        return payload["verdicts"]

    def _parse_verdict(self, entry: dict, entry_ids: set[str]) -> StitchVerdict | None:
        confidence = entry.get("confidence")
        if not isinstance(confidence, (int, float)):
            return None
        target_id = entry.get("target_id")
        if target_id is not None and target_id not in entry_ids:
            target_id = None
        return StitchVerdict(target_id=target_id, confidence=float(confidence))

    def _edges(
        self,
        candidates: tuple[EffectSite, ...],
        results: dict[str, StitchVerdict],
        entry_ids: set[str],
    ) -> tuple[FlowEdge, ...]:
        edges: list[FlowEdge] = []
        for candidate in candidates:
            verdict = results.get(candidate.id)
            if verdict is None or verdict.target_id is None or verdict.target_id not in entry_ids:
                continue
            edges.append(
                FlowEdge(
                    source=candidate.id,
                    target=verdict.target_id,
                    kind="stitch",
                    confidence="inferred",
                )
            )
        return tuple(edges)
