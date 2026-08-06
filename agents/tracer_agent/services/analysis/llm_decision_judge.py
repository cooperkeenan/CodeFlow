import json
import logging
import re

import anthropic
from models.decision_candidate import DecisionCandidate
from models.decision_verdict import DecisionVerdict
from prompts.decision_judge_prompt import DECISION_JUDGE_SYSTEM_PROMPT, build_decision_evidence
from services.analysis.decision_fingerprint import compute_fingerprint
from services.analysis.decision_judge import DecisionJudge
from services.analysis.verdict_cache import VerdictCache

logger = logging.getLogger(__name__)
_MODEL = "claude-haiku-4-5-20251001"
_BATCH_SIZE = 20
_VERDICT_MAP = {"decision": "decision", "guard": "guarded_step", "noise": "noise"}


class LlmDecisionJudge:
    def __init__(
        self,
        anthropic_client: anthropic.Anthropic,
        fallback: DecisionJudge,
        cache: VerdictCache,
    ) -> None:
        self._llm = anthropic_client
        self._fallback = fallback
        self._cache = cache

    def judge(self, candidates: tuple[DecisionCandidate, ...]) -> dict[str, DecisionVerdict]:
        fingerprints = {c.site_id: compute_fingerprint(c) for c in candidates}
        results: dict[str, DecisionVerdict] = {}
        groups: dict[str, list[DecisionCandidate]] = {}
        for candidate in candidates:
            fingerprint = fingerprints[candidate.site_id]
            cached = self._cache.get(fingerprint)
            if cached is not None:
                results[candidate.site_id] = cached
            else:
                groups.setdefault(fingerprint, []).append(candidate)
        representatives = sorted(
            (group[0] for group in groups.values()), key=lambda c: c.site_id
        )
        for start in range(0, len(representatives), _BATCH_SIZE):
            batch = representatives[start : start + _BATCH_SIZE]
            batch_verdicts, cacheable = self._judge_batch(batch)
            for candidate in batch:
                fingerprint = fingerprints[candidate.site_id]
                verdict = batch_verdicts[candidate.site_id]
                if candidate.site_id in cacheable:
                    self._cache.put(fingerprint, verdict)
                for duplicate in groups[fingerprint]:
                    results[duplicate.site_id] = verdict
        self._cache.flush()
        return results

    def _judge_batch(
        self, batch: list[DecisionCandidate]
    ) -> tuple[dict[str, DecisionVerdict], set[str]]:
        try:
            entries = self._call(batch)
        except Exception as exc:
            logger.warning("Decision judging fell back for batch of %d: %s", len(batch), exc)
            return self._fallback.judge(tuple(batch)), set()
        by_id = {c.site_id: c for c in batch}
        verdicts: dict[str, DecisionVerdict] = {}
        for entry in entries:
            site_id = entry.get("id")
            verdict = self._parse_verdict(entry)
            if verdict is None or site_id not in by_id:
                continue
            verdicts[site_id] = verdict
        cacheable = set(verdicts)
        missing = [c for c in batch if c.site_id not in verdicts]
        if missing:
            verdicts.update(self._fallback.judge(tuple(missing)))
        return verdicts, cacheable

    def _call(self, batch: list[DecisionCandidate]) -> list[dict]:
        response = self._llm.messages.create(
            model=_MODEL,
            max_tokens=4000,
            temperature=0,
            system=DECISION_JUDGE_SYSTEM_PROMPT,
            messages=[{"role": "user", "content": build_decision_evidence(tuple(batch))}],
        )
        text = next((b.text for b in response.content if b.type == "text"), "")
        match = re.search(r"\{.*\}", text, re.DOTALL)
        if not match:
            raise ValueError("LLM did not return valid JSON")
        payload = json.loads(match.group())
        return payload["verdicts"]

    def _parse_verdict(self, entry: dict) -> DecisionVerdict | None:
        verdict = _VERDICT_MAP.get(entry.get("verdict"))
        confidence = entry.get("confidence")
        if verdict is None or not isinstance(confidence, (int, float)):
            return None
        arm_labels = entry.get("arm_labels") or ()
        importance = entry.get("importance")
        if not isinstance(importance, (int, float)):
            importance = 0.0
        return DecisionVerdict(
            verdict=verdict,
            question=str(entry.get("question", "")),
            arm_labels=tuple(arm_labels),
            confidence=float(confidence),
            importance=float(importance),
        )
