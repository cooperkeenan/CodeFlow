# PBI 17 — Capture selection reasoning into meta + logs (layout)

**Batch:** 4 &nbsp;|&nbsp; **Depends on:** PBI 14 &nbsp;|&nbsp; **Read `README.md` first.**

## Why
Nothing records *why* a diagram type was chosen — the `select_diagram_template` tool only receives
`diagram_type`, so debugging a bad choice is guesswork. Force the model to articulate its reasoning
and store it where it can be read (file in PBI 18, UI in PBI 19).

## Scope

### 1. Selector tool schema — `agents/layout_agent/tools/select_diagram_template_tool.py`
Add a required `reasoning: str` field to `SELECT_DIAGRAM_TEMPLATE_SCHEMA.input_schema` (a short
explanation of why this type fits the evidence). The tool handler keeps validating/building on
`diagram_type`; it does not need to act on `reasoning`.

### 2. System-template planner — `agents/layout_agent/services/template_planner.py`
Read `reasoning` from the tool-use input and store it on the built template as
`DiagramTemplate.meta["rationale"]`. Log it alongside the existing "chosen type" log line.

### 3. Per-module cluster planner — `agents/layout_agent/prompts/cluster_prompt.py` + `services/cluster_planner.py`
The per-module call already returns a `diagram_type`. Add a `reasoning` field to that JSON schema in
`cluster_prompt.py`, and in `cluster_planner.py` store it in the corresponding module view's template
`meta["rationale"]` so module/component views carry a rationale too.

## Acceptance criteria
- Every entry in `diagram_templates` has a non-empty `meta["rationale"]` (system + module views).
- Selection remains deterministic at temperature 0.
- The decision trail still logs the chosen type; it now also logs the rationale.

## Out of scope
- Persisting the reasoning file (PBI 18) and rendering it in the UI (PBI 19).
