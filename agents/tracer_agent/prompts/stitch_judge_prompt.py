import json

from models.effect_site import EffectSite
from models.flow_entry import FlowEntry

PROMPT_VERSION = "1"

STITCH_JUDGE_SYSTEM_PROMPT = """You judge whether an outbound call in Python source is aimed at one of THIS repo's own services, or leaves the repo entirely.

You are given a directory of the repo's known entry routes, grouped by service, and a batch of outbound calls whose target could not be resolved to any of those routes by exact path matching. The target may be dynamic: a bare variable name, a partial path, or a base URL loaded at runtime (e.g. from config or a service registry).

For each call, decide whether the caller's fully-qualified name, the HTTP method, and any target text make ONE specific listed route the clear, confident destination. If so, return that route's id.

Return null whenever the call plausibly leaves the repo: a third-party vendor or cloud API, a database, a queue, telemetry, or any destination that cannot be pinned to a specific listed route with confidence. Returning null is the CORRECT answer far more often than not — do not force a match just because some service exists that could theoretically be involved. A wrong match is worse than no match.

Return STRICT JSON only: {"verdicts":[{"id":"<call id>","target_id":"<route id>|null","confidence":0.0-1.0}]}
"""


def build_stitch_evidence(
    candidates: tuple[EffectSite, ...], entries: tuple[FlowEntry, ...]
) -> str:
    return json.dumps({"services": _services(entries), "calls": [_call(c) for c in candidates]})


def _services(entries: tuple[FlowEntry, ...]) -> list[dict]:
    by_root: dict[str, list[FlowEntry]] = {}
    for entry in entries:
        by_root.setdefault(entry.service_root, []).append(entry)
    return [
        {"service": root, "routes": [_route(entry) for entry in members]}
        for root, members in sorted(by_root.items())
    ]


def _route(entry: FlowEntry) -> dict:
    return {
        "id": entry.id,
        "method": entry.method,
        "path": entry.path,
        "label": entry.label,
        "handler": entry.handler_fqn,
    }


def _call(effect: EffectSite) -> dict:
    return {
        "id": effect.id,
        "caller": effect.owner,
        "method": effect.method,
        "target": effect.target,
    }
