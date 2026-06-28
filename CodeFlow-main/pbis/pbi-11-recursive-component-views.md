# PBI 11 — Recursive component views + drillability correctness

**Phase:** 3. **Depends on:** Phase 2 (PBIs 7–10, done). **Read `README.md` first.**

## Why
Two live bugs at the component level, diagnosed and cross-confirmed against `outputs/render.json` + `outputs/layout.json`:

- **Drilling into a nested child blanks the page.** The component view marks every child `drillable: true`, but `ViewPlanner` only creates `component:<name>` views for **non-nested** components — one gate at `agents/layout_agent/services/view_planner.py:31` (`if not c.nested`). All 6 children of `TracerService` are `nested=True`, so no views exist; clicking → `views[viewId]` undefined → `useGraphTransform` returns `{nodes:[],edges:[]}` → blank. The real hierarchy is 4 levels deep (`TracerService → BuildEvidenceTool → EvidenceService → AstService`); all 10 nested components are unreachable.
- `build_component` (`_view_builder.py`) **already produces correct views for nested components** — verified by running it live. The only blocker is the filter.

This PBI is self-contained and delivers value before PBI 12/13 (drill-down works, no blanks, current `relationship` look retained).

## Scope

### 1. Generate views for all meaningful components — `agents/layout_agent/services/view_planner.py`
- Replace the `if not c.nested` filter (~line 31) with: **include a component iff it has `children` OR participates in ≥1 non-`import` call edge** (as source or target). This reaches nested components.
- Compute `view_set: set[str]` = the names of all components that get a `component:` view.
- Build a view for every component in `view_set` (nested included).

### 2. Drillability = "has a view" — single source of truth
- Add `drillable: bool = False` to `TemplateNode` in `shared/models/diagram_template.py` (or reuse a clearly-named existing field — do not overload `style`).
- Pass `view_set` into `_view_builder.build_component` and `build_module`. When emitting a caller/callee/child/component `TemplateNode`, set `drillable = (name in view_set)`. The focus node stays non-drillable.

### 3. Render placement honors the flag — `agents/render_agent/placement/`
- `relationship.py` and `module_view.py`: stop hardcoding drillability (`relationship.py` defaults `True`; `module_view.py` was hardcoded `True` in PBI-10 follow-up). Read `node.drillable` from the template node and pass it into the node `data`.

### 4. Frontend defensive guard (belt-and-suspenders)
- `frontend/src/components/diagram/DiagramExplorer.jsx` (click handler, ~line 33) or `frontend/src/hooks/useGraphTransform.js`: only navigate to a component when `views['component:'+label]` exists; otherwise open the detail panel (the existing `else` branch). A missing view must never blank the canvas.

## Acceptance criteria
- Drill `TracerService → BuildEvidenceTool → EvidenceService → AstService` works end to end; no blank pages anywhere.
- Leaf value-objects with no children/edges (e.g. `TracerResponse`) are **not** drillable — clicking opens the detail panel.
- The `views` map contains a `component:*` entry for every component with children or call relationships.
- Determinism preserved; no added LLM calls.

## Out of scope
- Choosing a per-component archetype (PBI 12) and placing it (PBI 13). Views keep `type="relationship"` for now.
