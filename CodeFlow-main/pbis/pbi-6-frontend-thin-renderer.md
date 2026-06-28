# PBI 6 — Frontend thin renderer (explicitly authorized)

**Depends on:** PBI 5. **Read `README.md` first.**

> This PBI touches `frontend/`. That is **explicitly authorized for this work package**, overriding the usual `CLAUDE.md` "do not modify frontend/" rule. Touch only what is listed here.

## Why
The system-level graph view should render the backend's deterministic positions instead of computing its own (dagre). This is where the user sees the consistency win. Module and component drill-down views are out of scope and must keep working unchanged.

## Scope

### 1. System graph hook — `frontend/src/hooks/graph/systemGraph.js`
- Stop computing positions. Consume the backend-supplied nodes/edges (already positioned) from the spec/response.
- Apply **only theme/styling** via the existing helpers in `frontend/src/hooks/graph/common.js` (`colorForModule` for node `data.color`, `toRFEdge` for edge styling/markers). The backend supplies `id`, `type` (`moduleSummary`), `position`, and structural `data`; the frontend fills color/markers.
- Remove the `dagre` import and the `positionMesh` / `positionModules` / `positionPipeline` / `positionHub` / `positionByRank` math.

### 2. Wire the backend graph through
- `frontend/src/pages/DiagramPage.jsx` → `frontend/src/components/diagram/DiagramExplorer.jsx` → `frontend/src/hooks/useGraphTransform.js`: pass the backend React Flow JSON (from `AnalyseResponse`, PBI 5) into the **system-focus branch** only (`!focus`). The branches for `focus.kind === 'module'` (`buildModuleGraph`) and component focus (`buildComponentGraph`) are **unchanged**.

### 3. Cleanup
- Delete the unused `frontend/src/components/MermaidDiagram.jsx`.
- Drop `dagre` and `mermaid` from `frontend/package.json` if no longer referenced anywhere.

## Acceptance criteria
- System view renders backend positions; a mesh-type repo is **stable across reloads** (no jitter).
- Drilling into a module and into a component still works exactly as before.
- `vite build` passes; no dangling imports of `dagre` / `mermaid` / `MermaidDiagram`.

## Out of scope
- Any change to `moduleGraph.js`, `clusterLayout.js`, `flatLayout.js`, `componentGraph.js`, or the node components.
