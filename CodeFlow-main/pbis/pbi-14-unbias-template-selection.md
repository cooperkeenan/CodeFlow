# PBI 14 — Unbias system template selection

**Batch:** 4 &nbsp;|&nbsp; **Depends on:** — &nbsp;|&nbsp; **Read `README.md` first.**

## Why
The layout agent picks `hub_and_spoke` for almost every view. One cause is a deterministic
**hint**: `TemplatePlanner` runs `ArchetypeClassifier` purely to inject an `archetype_hint` into the
LLM evidence. On this repo the module graph is edge-sparse, so the classifier falls through to a
default and that default primes every selection. The LLM should choose from the spec evidence
(modules, descriptions, module edges) — not be nudged by a low-signal hint.

## Scope

### 1. Evidence + prompt — `agents/layout_agent/prompts/template_prompt.py`
- Remove the `archetype` and `rationale` parameters from `build_evidence(...)`.
- Remove the `"archetype_hint"` key from the emitted evidence JSON.
- In `TEMPLATE_SYSTEM_PROMPT`, delete the trailing paragraph that explains the `archetype_hint`
  ("The archetype_hint comes from static analysis — use it as a starting signal…"). Keep the
  per-type guidance list intact.

### 2. Planner — `agents/layout_agent/services/template_planner.py`
- Stop calling `ArchetypeClassifier.classify(...)` and `ModuleGraphBuilder.build(...)` for the
  purpose of building the hint. Update the `build_evidence(...)` call site accordingly.
- Remove the now-unused constructor dependencies (`classifier`, `graph_builder`) if nothing else in
  the class uses them; otherwise leave them. Keep the existing logging of the **chosen** type.

### 3. DI — `agents/layout_agent/dependencies.py`
- Update `get_template_planner(...)` to match the trimmed constructor signature.

## Do NOT touch
- `agents/layout_agent/services/layout_service.py`. Its `ArchetypeClassifier` use produces
  `module_order` / `rank_assignments` for **placement** and is a separate concern — leave it.

## Acceptance criteria
- The evidence sent to `select_diagram_template` contains no archetype hint.
- Selection still runs at temperature 0 and returns a valid `DiagramTemplate`.
- `layout_hint.archetype` and placement output are unchanged from before this PBI.

## Out of scope
- Recovering edges (PBI 15), description quality (PBI 16), reasoning capture (PBI 17).
