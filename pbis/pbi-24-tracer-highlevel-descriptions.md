# PBI 24 — Rich purpose descriptions for high-level components (tracer)

**Batch:** 6 &nbsp;|&nbsp; **Depends on:** — &nbsp;|&nbsp; **Read `README.md` first.**

## Why
Component diagram types are chosen from **call-graph topology only**
(`helpers/component_archetype_classifier.py:19`): anything with ≥3 callees and ≤1 caller is forced to
`hub_and_spoke`, and `pipeline` can only fire for a *single* callee. So an orchestrator like
`TracerService` — which actually runs its six helpers **in sequence** (fetch → call-graph → evidence
→ trace → validate → correct → assemble) — is a star in the call graph and renders as hub_and_spoke.
The ordering/semantics that make it a pipeline exist nowhere in the data the layout agent sees. The
tracer already reads the code; have it describe each high-level component's purpose and the ordered
steps it coordinates, so the layout agent (PBI 25) can choose the right type from meaning, not topology.

## Scope

### 1. Prompt — `agents/tracer_agent/prompts/tracer_prompt.py`
For **high-level components** (entry points / orchestrators / any component with ≥2 callees or
children), instruct the LLM to produce a fuller `description`: 2–4 sentences covering what the
component does end-to-end **and the sequence of steps it coordinates, in order**. Leaf components keep
their existing short descriptions. Keep the strict-JSON contract and existing evidence rules.

### 2. Model / assembly
Reuse the existing `Component.description` field — no model change — and make the richer text survive
`services/spec_assembler.py` and the correction loop. (If a separate field reads cleaner, add
`purpose: str = ""` to `Component` in `shared/models/diagram_spec.py`; reuse is preferred.)

## Acceptance criteria
- High-level components in the tracer output carry a multi-sentence description that names their
  ordered steps; leaf components keep short descriptions.
- No regression to component/edge discovery or the recovered cross-module edges.

## Out of scope
- The layout-side type selection that consumes these descriptions (PBI 25).
- Any render changes.
