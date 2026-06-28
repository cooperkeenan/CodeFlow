# PBI 25 — Description-driven component template selection (layout)

**Batch:** 6 &nbsp;|&nbsp; **Depends on:** PBI 24 &nbsp;|&nbsp; **Read `README.md` first.**

## Why
Replace the topology-only `ComponentArchetypeClassifier` for **high-level** components with a choice
driven by the rich descriptions from PBI 24, so a sequential orchestrator becomes `pipeline` and a
true fan-out dispatcher stays `hub_and_spoke`. Leaf components stay deterministic (no LLM needed).

## Scope

### 1. Prompt — `agents/layout_agent/prompts/component_type_prompt.py` (new)
System prompt instructing the LLM to choose one `DiagramType` per high-level component from its
description + local graph, and — when the type is sequential (`pipeline`/`hierarchy`) — return the
ordered node sequence. Temperature 0; strict JSON; deterministic phrasing.

### 2. Planner — `agents/layout_agent/services/component_type_planner.py` (new)
Constructor-injected `anthropic.AsyncAnthropic`. **One batched LLM call** over all high-level
components (those in `view_set` with ≥2 callees+children, or role `orchestrator`/`entry`) — NOT one
call per component. Input per component: name, rich `description`, `callers`, `callees`, `children`,
and the candidate types + their descriptions. Output JSON: `{component: {type, reasoning, order?}}`.
Validate `type` against `DiagramType` and `order` against that component's own node set; fall back to
the deterministic `ComponentArchetypeClassifier` for any component the LLM omits or returns invalid.

### 3. Wire-in — `agents/layout_agent/services/_view_builder.py:build_component`
For high-level components, use the planner's result instead of `self._classifier.classify(...)`:
- set `DiagramTemplate.type` from the planner;
- store `reasoning` in `meta["rationale"]` (the `RationaleBox` already renders this — component views
  currently show no rationale);
- when `order` is provided, reorder `template.nodes` to that sequence so the existing
  `component_pipeline` placement (Batch 5) draws the real left→right chain.
Keep the deterministic classifier for all non-high-level components.

### 4. DI — `agents/layout_agent/dependencies.py`
Inject the planner into the view builder / view planner; run the batched call once per `/layout`.

> Keep every file ≤150 lines; split a helper if needed. Constructor injection only.

## Acceptance criteria
- `TracerService` (and similar sequential orchestrators) classify as `pipeline` with a populated
  `meta["rationale"]` and a sensible ordered chain; genuine dispatchers stay `hub_and_spoke`.
- Leaf components are unchanged; selection is one batched LLM call at temperature 0 (repeatable).
- Component views now show a rationale in the UI.

## Out of scope
- Module/system selection. Render placement changes (reuse the existing `component_<type>` placements).
