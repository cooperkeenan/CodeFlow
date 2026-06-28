# PBI 12 — Component-level archetype classifier + selection (layout side)

**Phase:** 3. **Depends on:** PBI 11. **Pairs with:** PBI 13. **Read `README.md` first.**

## Why
The component view currently **hardcodes** `type="relationship"` (`_view_builder.py:68,95`) — it never runs the classifier/selector the system and module views use, so the component level bypasses the template library. The user wants the component level to genuinely select a template (Option B), chosen from each component's local graph. Selection must stay **deterministic** (no per-component LLM call — that would reintroduce the ~230-call explosion Phase 2 avoided).

## Scope

### 1. New `ComponentArchetypeClassifier` — `agents/layout_agent/helpers/component_archetype_classifier.py`
- Input: the component's local subgraph already assembled in `build_component` — `focus`, `callers`, `callees`, `children`, and the edges among them.
- Output: a `DiagramType`.
- Deterministic heuristics over the local graph (mirror the signal style of the module-level `helpers/archetype_classifier.py`: fan-in/out, chain length):
  - linear `caller → focus → callee` chain, low fan → `pipeline`
  - focus with many callees/children and few/no callers → `hub_and_spoke`
  - children forming a visible sub-tree (depth ≥ 2 within the included set) → `hierarchy`
  - otherwise (mixed callers + callees + children, no dominant shape) → `relationship` (fallback)
- Pure/stateless; constructor injection if it needs config. ≤150 lines.

### 2. Use the classifier in `_view_builder.build_component`
- Stop hardcoding `type="relationship"`. Call the classifier, set `type` to its result.
- Build the `meta` the chosen archetype's placement needs, consistent with `_template_builder._build_meta` for modules: e.g. `hub_id`=focus for `hub_and_spoke`; `depth_map` for `hierarchy`; keep `focus`/`callers`/`callees`/`children` in meta for `relationship`.

### 3. Formalize `relationship` as a first-class template
- Add a `relationship` definition under `agents/layout_agent/templates/` and register it in the layout-side `TemplateRegistry`.
- Include `relationship` in the selectable set where appropriate (e.g. `cluster_planner._VALID_TYPES` if it should ever be module-selectable; at minimum make it a legitimate registry entry so it's no longer "a template that is never selected").

## Acceptance criteria
- A tree-shaped component renders as `hierarchy`; a one-to-many fan as `hub_and_spoke`; a chain as `pipeline`; a mixed neighborhood as `relationship`.
- Selection is **deterministic** — identical type across runs for the same spec.
- **No added LLM calls** — verify layout-agent call count stays `1 + N_modules + 1`.
- `relationship` is a registered template, not a hardcoded special case.

## Out of scope
- Render-side placement of the selected archetypes for component nodes (PBI 13). This PBI only sets `type` + `meta`.
