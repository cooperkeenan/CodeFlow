import hashlib
import json

from tracer.models.naming import NodeNameContext
from tracer.models.sites import EffectSite, FlowEntry
from tracer.models.verdicts import DecisionCandidate
from tracer.prompts.decision_judge_prompt import (
    PROMPT_VERSION as _DECISION_PROMPT_VERSION,
)
from tracer.prompts.flow_name_prompt import PROMPT_VERSION as _NAME_PROMPT_VERSION
from tracer.prompts.flow_review_prompt import PROMPT_VERSION as _REVIEW_PROMPT_VERSION
from tracer.prompts.stitch_judge_prompt import PROMPT_VERSION as _STITCH_PROMPT_VERSION

_SEPARATOR = "\x1f"


def compute_name_fingerprint(context: NodeNameContext) -> str:
    node = context.node
    parts = [
        _NAME_PROMPT_VERSION,
        node.kind,
        node.label,
        *sorted(node.backing),
        *context.arm_label_sources,
        node.effect_kind or "",
        node.effect_target or "",
        *sorted(context.child_labels),
    ]
    return hashlib.sha256(_SEPARATOR.join(parts).encode("utf-8")).hexdigest()


def compute_review_fingerprint(bundle: list[dict]) -> str:
    serialized = json.dumps(bundle, sort_keys=True)
    payload = _SEPARATOR.join([_REVIEW_PROMPT_VERSION, serialized])
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def compute_decision_fingerprint(candidate: DecisionCandidate) -> str:
    parts = [
        _DECISION_PROMPT_VERSION,
        candidate.site.kind,
        candidate.source_snippet,
        *(arm.label_source for arm in candidate.site.arms),
        *(str(size) for size in candidate.arm_reach_sizes),
    ]
    return hashlib.sha256(_SEPARATOR.join(parts).encode("utf-8")).hexdigest()


def compute_stitch_fingerprint(effect: EffectSite, entries: tuple[FlowEntry, ...]) -> str:
    parts = [
        _STITCH_PROMPT_VERSION,
        effect.owner,
        effect.method,
        effect.target,
        *(f"{entry.id}:{entry.method}:{entry.path}" for entry in sorted(entries, key=lambda e: e.id)),
    ]
    return hashlib.sha256(_SEPARATOR.join(parts).encode("utf-8")).hexdigest()
