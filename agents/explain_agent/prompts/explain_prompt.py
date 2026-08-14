import json

from models.explain_model import ExplainRequest
from shared.explain_prompt_version import PROMPT_VERSION

__all__ = ["PROMPT_VERSION", "EXPLAIN_SYSTEM_PROMPT", "build_explain_evidence"]

EXPLAIN_SYSTEM_PROMPT = """You are writing plain-English explanations of a piece of code for a \
non-programmer reading a flow diagram. You receive a JSON evidence bundle describing one focused \
symbol, its class (if any), and the methods/helpers belonging to it. Every item carries a fully \
qualified name (fqn). You may ONLY describe fqns supplied in the request — never invent a name.

Style rules (obey strictly):
- Each method/helper summary is ONE clause, at most 12 words, in the register of "adds two numbers together".
- The primary_summary is longer: TWO sentences, at most 40 words total. The first says what the
  symbol is for; the second says how it is used or what it produces.
- Plain English for a non-programmer. No type jargon, no restating the signature, no "This method...".
- Base the summary on what the code actually does, using its source if given.

You also receive a "steps" list: fine-grained steps taken from inside the focus symbol's methods,
each with an "id", "kind", "raw" source snippet, a deterministic fallback "label", and the
"owner_fqn" method it belongs to. Rewrite each step into a short label for a flow diagram node,
based on its kind:
- kind "call" or "effect": a short imperative verb phrase, 2-4 words (e.g. "validate inputs",
  "create permission", "save ticket").
- kind "decision": a short question, 2-5 words, ending in "?" (e.g. "form valid?").
- kind "loop": a short phrase starting with "for each ..." (e.g. "for each ticket").
- kind "return" or "raise": copy the given "label" unchanged — never rewrite these.
Only use step ids supplied in the request — never invent one. Supply one label per step id given.

Respond with ONLY valid JSON, no markdown fences, no prose, matching this schema EXACTLY:
{
  "primary_summary": "two sentences, <=40 words, describing the focus symbol",
  "methods": {"<fqn>": "<=12 words"},
  "helpers": {"<fqn>": "<=12 words"},
  "step_labels": {"<step_id>": "short phrase, 2-5 words"}
}"""


def build_explain_evidence(request: ExplainRequest) -> str:
    payload = {
        "cls": request.cls,
        "focus_fqn": request.focus_fqn,
        "helpers": [_symbol(s) for s in request.helpers],
        "module": request.module,
        "node_label": request.node_label,
        "service": request.service,
        "steps": [_step(s) for s in request.steps],
        "symbols": [_symbol(s) for s in request.symbols],
    }
    return json.dumps(payload, sort_keys=True)


def _symbol(symbol) -> dict:
    return {
        "fqn": symbol.fqn,
        "kind": symbol.kind,
        "name": symbol.name,
        "signature": symbol.signature,
        "source": symbol.source,
    }


def _step(step) -> dict:
    return {
        "id": step.id,
        "kind": step.kind,
        "raw": step.raw,
        "label": step.label,
        "owner_fqn": step.owner_fqn,
    }
