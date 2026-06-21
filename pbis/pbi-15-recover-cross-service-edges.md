# PBI 15 — Recover cross-service HTTP edges (tracer)

**Batch:** 4 &nbsp;|&nbsp; **Depends on:** — &nbsp;|&nbsp; **Read `README.md` first.**

## Why
The system module-graph has **zero cross-module edges**: all traced edges are intra-module because
the evidence bundle is `jarviscg` (in-process call graph) ∩ AST imports, and neither sees network
calls. `agents/tracer_agent/services/ast_service.py` only extracts uppercase imports — it never
parses `httpx`/`requests` calls or URL strings. So the real cross-service calls in
`api/clients/*_client.py` (`api → {profiler,tracer,layout,render}_agent`) never reach the spec, and
the layout agent chooses a system diagram type for a graph with no connections.

The tracer prompt *already* defines an `http` edge type for "client wrappers hitting a URL", and the
`Edge` model already supports `edge_type="http"`. The missing piece is **evidence**: give the LLM
HTTP-call facts to back those edges, and stop the validator from rejecting them.

## Scope
> Mirror the multi-step style of PBI 3/4. Keep every file ≤150 lines — extract a small private
> helper/service if a file would exceed it (e.g. an `HttpCallVisitor`).

### 1. Detect HTTP calls — `agents/tracer_agent/services/ast_service.py`
Add an AST pass that finds outbound HTTP calls and returns `(caller_component, target)` pairs:
- method calls like `httpx.post(...)`, `client.post(...)`, `requests.get(...)`, `await ...post(url, ...)`;
- the target derived from the URL/argument — a settings constant (e.g. `LAYOUT_AGENT_URL`), a path
  literal, or the client class name — normalised to a service identifier the LLM can map to a module.
- Attribute the call to the enclosing class (the caller component), consistent with how existing
  signatures are scoped.

### 2. Expose evidence — `agents/tracer_agent/services/evidence_service.py`
Add an `http_edges` list to the evidence bundle returned by `build(...)`, alongside the existing
`signatures` / `import_edges` / `call_edges` / `confirmed_edges`. Each entry: `{from, to}` (plus the
raw URL/hint if useful for the LLM to resolve the target).

### 3. Prompt — `agents/tracer_agent/prompts/tracer_prompt.py`
Update the EVIDENCE RULES so an `http` edge may be backed by `evidence.http_edges` (not only
in-process `call_edges`). Instruct the LLM to resolve each HTTP target to the **receiving service's
entry-point component / module** so the edge crosses module boundaries.

### 4. Validator — `agents/tracer_agent/services/graph_validator.py`
Include `http_edges` in the evidence-pair set used by the `W3` "edge not in evidence" check so
legitimate cross-service edges no longer warn.

### 5. Assembly — `agents/tracer_agent/services/spec_assembler.py`
Confirm cross-module `http` edges survive `_edges(...)` (both endpoints must resolve to known
component names in different modules). Adjust only if assembly currently drops them.

## Acceptance criteria
- Running `/trace` (or `/analyse`) on this repo yields ≥1 **cross-module** edge in
  `diagram_spec.edges` (e.g. `api → *_agent`), verifiable by collapsing component edges to modules.
- Existing intra-module `call` edges are unchanged.
- No `W3` validator warning fires on the recovered HTTP edges.

## Out of scope
- Changing the `Edge` model shape. Use the existing `edge_type="http"`.
- Layout-side description/selection changes (PBIs 16/14).
