import json

from models.explain_model import ExplainRequest
from shared.explain_prompt_version import PROMPT_VERSION

__all__ = ["PROMPT_VERSION", "EXPLAIN_SYSTEM_PROMPT", "build_explain_evidence"]

EXPLAIN_SYSTEM_PROMPT = """You are writing plain-English explanations of a piece of code for a \
non-programmer reading a flow diagram. You receive a JSON evidence bundle describing one focused \
symbol, its class (if any), and the methods/helpers belonging to it. Every item carries a fully \
qualified name (fqn). You may ONLY describe fqns supplied in the request — never invent a name.

Style rules (obey strictly):
- Each summary is ONE clause, at most 12 words, in the register of "adds two numbers together".
- Plain English for a non-programmer. No type jargon, no restating the signature, no "This method...".
- Base the summary on what the code actually does, using its source if given.

Respond with ONLY valid JSON, no markdown fences, no prose, matching this schema EXACTLY:
{
  "primary_summary": "<=12 words summarizing the focus symbol",
  "methods": {"<fqn>": "<=12 words"},
  "helpers": {"<fqn>": "<=12 words"}
}"""


def build_explain_evidence(request: ExplainRequest) -> str:
    payload = {
        "cls": request.cls,
        "focus_fqn": request.focus_fqn,
        "helpers": [_symbol(s) for s in request.helpers],
        "module": request.module,
        "node_label": request.node_label,
        "service": request.service,
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
