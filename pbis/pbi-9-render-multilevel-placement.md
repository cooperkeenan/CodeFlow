# PBI 9 — Render agent: placement for module + component views

**Phase:** 2. **Depends on:** PBI 7 (schema), PBI 8 (specs). **Read `README.md` first.**

## Why
Backend owns all placement now. The render agent must deterministically place the module-interior and component views — and crucially emit **edges at every level**, since that is where the real graph lives (the "floating components, no lines" symptom is the absence of rendered edges at the module level, where intra-module edges actually exist).

## Scope

### 1. Module-view placement — port from frontend
- Port `frontend/src/hooks/graph/clusterLayout.js` (+ `flatLayout.js` for modules without `cluster_plan`) into Python placement under `agents/render_agent/placement/`.
- Produce nested React Flow nodes: `zoneGroup` and `clusterGroup` container nodes with `parentNode` + `extent: "parent"`, and member `custom` component nodes positioned inside, laid out per the cluster `style`.
- Port the per-style member math **and member edges** from `frontend/src/hooks/graph/templates/` (`gridTemplate`, `stackTemplate`, `pipelineTemplate`, `hierarchyTemplate`, `hubTemplate`): pipeline → consecutive edges, hierarchy → root→children, hub → hub→spokes, grid/stack → no member edges.

### 2. Component-view placement — port from frontend
- Port `frontend/src/hooks/graph/componentGraph.js` 3-column math: callers (left) → focus (center) → callees (right), children below. Type key `"relationship"`.

### 3. Edges at every level
- Module view: emit the template's intra-module `edges` plus the template-style member edges, using the id/source/target conventions already in `PlacementService._build_edges` and the `toRFEdge` shape (no styling — frontend themes).
- Component view: emit the neighbor/contains edges from the template.

### 4. Service + registry
- `PlacementService.render` accepts `dict[viewId, DiagramTemplate]` and returns `dict[viewId, RenderedView]` (`{type, nodes, edges}` per view).
- Register the new placement functions in `agents/render_agent/placement/registry.py`, keyed including `"relationship"` and a module-view placer. Keep the six system-level placers.
- Use dimension constants consistent with frontend `common.js` (`NODE_W=180`, `NODE_H=58`, `MOD_W=240`, `MOD_H=110`, gaps) so visuals match.

## Acceptance criteria
- A module with N components returns nested group nodes + positioned components + **non-empty edges** when intra-module edges exist.
- Component view returns the 3-column relationship layout with caller/callee/child edges.
- Identical `DiagramTemplate` spec → identical positions (deterministic; no dagre, no randomness).
- Node/edge shapes match what `frontend/src/components/diagram/FlowGraph.jsx` and its node components expect (minus theme styling).

## Out of scope
- Theme/colors/markers (frontend, PBI 10).
- Cross-module edges in the system view (separate tracer follow-up).
