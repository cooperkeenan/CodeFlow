import json

from explain.models.contract_model import ContractRequest

from shared.contract_prompt_version import PROMPT_VERSION

__all__ = ["CONTRACT_SYSTEM_PROMPT", "PROMPT_VERSION", "build_contract_evidence"]

CONTRACT_SYSTEM_PROMPT = """You are writing an API contract for one HTTP endpoint, for a reader \
who wants to call it. You receive a JSON evidence bundle with the endpoint's handler source and \
any helper functions it calls.

The "method" and "path" fields in the evidence are FIXED FACTS, already determined by static \
analysis. You must echo them back UNCHANGED in your response — never invent, correct, or rewrite \
them.

From the handler and helper source, work out:
- params: every path, query, header, or body parameter you can actually see used, each with a
  "location" of exactly "path", "query", "header", or "body".
- request_body: a short description of the expected request body shape, or "" if none is read.
- responses: one entry per distinct status code the handler can return, each with "status" and a
  short "description"; add "shape" only if the response body shape is visible.
- auth: a short description of the auth/permission check performed, or "" if none is visible.
- example_request / example_response: a short, realistic example, or "" if you cannot construct
  one from the evidence.

If you cannot see enough evidence to fill a field, leave it empty ("" or an empty list) rather
than inventing a plausible-looking value.

Respond with ONLY valid JSON, no markdown fences, no prose, matching this schema EXACTLY:
{
  "method": "<echoed unchanged>",
  "path": "<echoed unchanged>",
  "summary": "one short sentence describing what the endpoint does",
  "params": [{"name": "...", "location": "path|query|header|body", "type": "...", "required": true, "description": "..."}],
  "request_body": "",
  "responses": [{"status": "200", "description": "...", "shape": ""}],
  "auth": "",
  "example_request": "",
  "example_response": ""
}"""


def build_contract_evidence(request: ContractRequest) -> str:
    payload = {
        "method": request.method,
        "path": request.path,
        "handler_fqn": request.handler_fqn,
        "path_params": sorted(request.path_params),
        "label": request.label,
        "symbols": [_symbol(s) for s in request.symbols],
        "helpers": [_symbol(s) for s in request.helpers],
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
