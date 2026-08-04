import hashlib
import json

from prompts.flow_review_prompt import PROMPT_VERSION

_SEPARATOR = "\x1f"


def compute_review_fingerprint(bundle: list[dict]) -> str:
    serialized = json.dumps(bundle, sort_keys=True)
    payload = _SEPARATOR.join([PROMPT_VERSION, serialized])
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()
