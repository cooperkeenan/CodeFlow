# PBI 8 — Layout agent: build a template spec per view (fold-in type selection)

**Phase:** 2. **Depends on:** PBI 7. **Read `README.md` first.**

## Why
Every level should be driven by the LLM's understanding of the code — but at ~0 added cost. The layout agent **already** makes one LLM call per module (`ClusterPlanner`, `agents/layout_agent/services/cluster_planner.py:31-47`) that reads each component's `role`, `tier`, `description`, `fan_in`, `fan_out`, and the intra-module edges. We harvest the module's diagram type from that existing call instead of adding new ones. The component view needs no LLM call (fixed relationship layout) — this is what avoids a per-component call explosion.

## Scope

### 1. Extend `ClusterPlanner` — fold in the module type (no new LLM call)
- `prompts/cluster_prompt.py`: instruct the model to also return a top-level `diagram_type` (one of the 6 `DiagramType` values) for the module, justified by the same evidence it already gets.
- `services/cluster_planner.py`: parse `diagram_type` from the response; validate against `TemplateRegistry`. On miss/failure, deterministic fallback — derive from the dominant cluster `style` (e.g. mostly `pipeline` clusters → `pipeline`; a dominant hub → `hub_and_spoke`; else `dependency_graph`). Store the chosen type so `ViewPlanner` can read it (e.g. on the module or a side map).

### 2. New `ViewPlanner` service — `agents/layout_agent/services/view_planner.py`
Assembles `dict[viewId, DiagramTemplate]`:
- **`system`**: reuse the existing `TemplatePlanner` output (Phase 1).
- **`module:<name>`** (per module): a `DiagramTemplate` with
  - `type` = the module's folded-in `diagram_type`,
  - `nodes` = zone group nodes (`kind="zone"`), cluster group nodes (`kind="cluster"`, `style` from `cluster_plan`), and component nodes (`kind="component"`, `parent` = their cluster/zone id), built from `module.zones` + `module.cluster_plan`,
  - `edges` = intra-module edges — reuse the exact filter in `ClusterPlanner._evidence` (`cluster_planner.py:58-62`): `e.source in names and e.target in names and e.source != e.target`,
  - `meta` = grouping info needed for placement (zone order, cluster membership).
- **`component:<name>`** (per non-nested component): a `DiagramTemplate` with `type="relationship"`,
  - `nodes` = callers + the focus component + callees + children,
  - `edges` = neighbor edges from `spec.edges` (port the selection logic from `frontend/src/hooks/graph/componentGraph.js`: exclude `import`, both endpoints in the involved set, no self-loops; plus contains-edges to children).

### 3. Wire-up
- `routers/layout.py`: after `cluster_planner.plan(...)`, call `view_planner.plan(spec)`; `LayoutResponse.diagram_templates: dict[str, DiagramTemplate]` (replaces the single `diagram_template`).
- Register `ViewPlanner` in `dependencies.py`.

## Acceptance criteria
- `diagram_templates` contains `system`, one `module:*` per module, and one `component:*` per non-nested component; counts match the spec.
- Module specs carry non-empty `edges` wherever the trace has intra-module edges (e.g. `module:layout_agent`).
- **LLM call count is unchanged** vs. today: `1` (semantic) + `N_modules` (cluster) + `1` (system template). No per-component calls. Verify by counting.
- Type selection is repeatable at temperature 0.

## Out of scope
- Placement/coordinates (PBI 9). `ViewPlanner` emits structure + type + meta only.
