# PBI 4 — Render agent placement engine (template → React Flow JSON)

**Depends on:** PBI 1 (schema). Can run in parallel with PBIs 2–3. **Read `README.md` first.**

## Why
The render agent finally earns its name: it consumes a `DiagramTemplate` and produces **deterministic** React Flow positions, replacing both the dead Mermaid path and the frontend's non-deterministic dagre mesh.

## Scope

### 1. Placement functions — `agents/render_agent/placement/` (new package, one file per type)
Six placement functions (`pipeline.py`, `hub_and_spoke.py`, `layered_tier.py`, `hierarchy.py`, `mesh.py`, `dependency_graph.py`). Each takes a `DiagramTemplate` and returns positioned React Flow nodes for its type, unpacking its own `meta` keys.
- Port the proven deterministic math from `frontend/src/hooks/graph/systemGraph.js`: `positionPipeline` (linear), `positionHub` (radial, hub at center from `meta.hub`), `positionByRank` (layered/hierarchy from tier/depth in `meta`).
- **Replace dagre `positionMesh` with a deterministic layout** — e.g. a stable grid or ordered rows derived from node order. No randomness, no force-directed library. (This is the core fix.)
- Reuse the dimension constants from frontend `common.js` (`MOD_W=240`, `MOD_H=110`, `MOD_GAP_X=110`, `MOD_GAP_Y=130`) so positions match the existing visual scale.

### 2. Registry — `agents/render_agent/placement/registry.py` (new)
`PlacementRegistry` mapping `DiagramType` → placement function, mirroring the layout-side registry. Adding a type later = one function + one registration.

### 3. Placement service — `agents/render_agent/services/placement_service.py` (new)
`PlacementService`, constructor-injected with `PlacementRegistry`. `render(template: DiagramTemplate) -> {nodes, edges}`:
- nodes: `{ id, type, position: {x, y}, data: {...} }` — **structure + positions only, no colors/markers** (frontend owns theme; see README contract). `type` should be `"moduleSummary"` to match the existing frontend node component.
- edges: `{ source, target, edge_type, label? }` — structural; aggregate/label like frontend `toModuleEdge` but **without** styling.

### 4. Replace the Mermaid path
- `agents/render_agent/models/render_model.py`: `RenderRequest` now carries `diagram_template: DiagramTemplate` (drop or keep `architecture_type` as needed); `RenderResponse` carries React Flow JSON (e.g. `nodes: list[dict]`, `edges: list[dict]`) instead of `mermaid`.
- `agents/render_agent/routers/render.py` + `dependencies.py`: wire `PlacementService` instead of `MermaidService`.
- Remove `MermaidService`, `ModuleRenderer`, `EdgeRenderer`, `ClusterRenderer`, `mermaid_ids.py`, and the empty `agent_executor.py` if fully unused after rewiring. (If a Mermaid export is still wanted, keep it behind a separate endpoint — default is removal.)

## Acceptance criteria
- Each of the 6 types produces stable, non-overlapping positions; identical `DiagramTemplate` in → identical coordinates out.
- No dagre / no randomness anywhere in the system-level render path.
- Node/edge shape matches what `frontend/src/components/diagram/FlowGraph.jsx` expects (minus styling).
- Render agent imports cleanly; no dangling references to removed Mermaid modules.

## Out of scope
- Module-interior and component placement (still frontend, unchanged).
- Theme/colors/markers (frontend, PBI 6).
