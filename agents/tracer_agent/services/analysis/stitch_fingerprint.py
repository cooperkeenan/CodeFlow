import hashlib

from models.effect_site import EffectSite
from models.flow_entry import FlowEntry
from prompts.stitch_judge_prompt import PROMPT_VERSION

_SEPARATOR = "\x1f"


def compute_stitch_fingerprint(effect: EffectSite, entries: tuple[FlowEntry, ...]) -> str:
    parts = [
        PROMPT_VERSION,
        effect.owner,
        effect.method,
        effect.target,
        *(f"{entry.id}:{entry.method}:{entry.path}" for entry in sorted(entries, key=lambda e: e.id)),
    ]
    return hashlib.sha256(_SEPARATOR.join(parts).encode("utf-8")).hexdigest()
