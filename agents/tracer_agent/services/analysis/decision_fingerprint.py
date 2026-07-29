import hashlib

from models.decision_candidate import DecisionCandidate

_SEPARATOR = "\x1f"


def compute_fingerprint(candidate: DecisionCandidate) -> str:
    parts = [
        candidate.site.kind,
        candidate.source_snippet,
        *(arm.label_source for arm in candidate.site.arms),
        *(str(size) for size in candidate.arm_reach_sizes),
    ]
    return hashlib.sha256(_SEPARATOR.join(parts).encode("utf-8")).hexdigest()
