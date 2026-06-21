# PBI 32 — Role-based service surfacing + adapter contraction (layout)

**Batch:** 10 &nbsp;|&nbsp; **Depends on:** Batch 7 (`_edge_builder`) &nbsp;|&nbsp; **Read `README.md` first.**

## Why
Higher-level pipelines currently surface thin adapter/tool nodes (`BuildCallGraphTool`) instead of the
meaningful business components (`CallGraphService`). A tool whose own rationale is *"simple helper
tool with a single callee (CallGraphService)"* is a pass-through and should be **folded into** the
service it wraps, so the high-level view reads `TracerService → CallGraphService → EvidenceService → …`.

The signal is the tracer's existing `role` field — surface primary roles, fold single-callee adapters.
This is generic (works for `*Service`, `*Manager`, `*Repository`, …) and **deterministic** (a graph
operation, no LLM); the resulting service order reuses the LLM ordering from Batch 6/7.

## Scope

### 1. Contraction helper — `agents/layout_agent/services/_graph_contraction.py` (new)
Given the component graph + roles, produce a **contracted graph** for higher-level views:
- **Primary** (surfaced): roles `service` / `orchestrator` / `repository` (and `entry`).
- **Adapter** (fold candidate): roles `tool` / `client` / `helper` **with exactly one callee** → fold
  the adapter into that callee; record it under the survivor's folded-members list (for PBI 33).
- **Guard:** an adapter with ≥2 callees (a real fan-out) is NOT folded — it stays visible.
- Re-point edges through folded nodes so the contracted graph connects survivors only.
Keep ≤150 lines.

### 2. Apply to higher-level views — `agents/layout_agent/services/_view_builder.py`
For module and orchestrator-component views, build the structure over the **contracted** graph, then
reuse the Batch 7 `_edge_builder` for ordering/edges. Store the folded members per surviving node in
`meta` (e.g. `meta["folded"] = {service: [adapter, ...]}`) for the drill-down container.

## Acceptance criteria
- The `tracer_agent` / `TracerService` view shows service→service (`CallGraphService → EvidenceService → …`)
  with the single-callee tools folded away; each surviving service records its folded members.
- A multi-callee tool is not folded. Leaf/relationship views unaffected. Deterministic at temperature 0.

## Out of scope
- The container drill-down rendering (PBI 33).
