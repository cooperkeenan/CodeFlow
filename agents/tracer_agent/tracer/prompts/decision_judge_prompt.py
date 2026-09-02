import json

from tracer.models.verdicts import DecisionCandidate

PROMPT_VERSION = "2"

DECISION_JUDGE_SYSTEM_PROMPT = """You judge whether a fork in Python source is a DECISION a human would put on a mental-model diagram of the system.

A DECISION is a branch point where the program chooses between genuinely different courses of action that a reader would need to know about to understand what the system does. Examples: choosing which service/handler/strategy to use, granting vs denying access, selecting a data source, routing work down materially different paths.

NOT a decision (these are "guard" or "noise"):
- null/None checks, empty-collection checks, hasattr/isinstance defensiveness
- early returns and raises that only validate input
- logging, telemetry, formatting, string building, serialization branches
- caching hits/misses, retry and error handling
- trivial defaulting (x = a if a else b)

For every decision, also rate "importance": 0.0-1.0, how central this decision is to understanding what the system does. Rank high: routing between services/agents/strategies, access and permission decisions, choosing which data source to read from. Rank low: error handling, retries and fallbacks — even when they are a genuine decision, they are not central to the mental model. Non-decisions ("guard"/"noise") should get importance 0.0.

Return STRICT JSON only: {"verdicts":[{"id":"<id>","verdict":"decision|guard|noise","question":"<the question a human would ask, 2-6 words, only if decision>","arm_labels":["..."],"confidence":0.0-1.0,"importance":0.0-1.0}]}
"question" must read like a question on a flowchart, e.g. "Service principal allowed?", "Which data source?"."""


def build_decision_evidence(candidates: tuple[DecisionCandidate, ...]) -> str:
    return json.dumps([_candidate(candidate) for candidate in candidates])


def _candidate(candidate: DecisionCandidate) -> dict:
    site = candidate.site
    return {
        "id": candidate.site_id,
        "where": f"{site.span.file}:{site.span.line}",
        "kind": site.kind,
        "enclosing_function": _enclosing_function(site.owner),
        "arm_reach_sizes": list(candidate.arm_reach_sizes),
        "source": candidate.source_snippet,
    }


def _enclosing_function(owner: str) -> str:
    return owner.rsplit(".", 1)[-1]
