# PBI 18 — Persist a readable reasoning file (api)

**Batch:** 4 &nbsp;|&nbsp; **Depends on:** PBI 17 &nbsp;|&nbsp; **Read `README.md` first.**

## Why
A single readable file is the easiest way to inspect every view's reasoning after a run, without
scrolling logs or clicking through the UI. PBI 17 puts the rationale in
`diagram_templates[viewId].meta["rationale"]`; project it into one file.

## Scope

### 1. Orchestration — `api/services/analysis_service.py`
After the layout step (where `diagram_templates` is available), build a reasoning projection:
`{ viewId → { type, rationale, modules, edges } }`, reading `type` and `meta["rationale"]` from each
template (and the per-view node/edge counts already present). Write it via the persister as
`layout_reasoning.json`. This is a pure projection of existing data — **no new agent calls**.

### 2. Persister — `api/services/output_persister.py`
Reuse the existing `write_json(...)` pattern (as used for `profiler.json` / `layout.json`) to write
`layout_reasoning.json` into the same `shared/outputs/` location.

## Acceptance criteria
- Running `/analyse` writes `shared/outputs/layout_reasoning.json` with one entry per view, each
  showing the chosen `type` and its `rationale`.
- No new LLM/agent calls are added; the file is derived from existing layout output.

## Out of scope
- Frontend rendering (PBI 19) and the reasoning capture itself (PBI 17).
