# PBI 10 — Frontend: consume the view map; retire client-side placement

**Phase:** 2. **Depends on:** PBI 9. **Read `README.md` first.**

> Touches `frontend/` — **explicitly authorized for this work package** (overrides the usual `CLAUDE.md` rule). Touch only what is listed.

## Why
Single source of truth: with the backend placing every level, the frontend stops computing layout and becomes a pure renderer. This is where the user sees connected, consistent diagrams at every level.

## Scope

### 1. `frontend/src/hooks/useGraphTransform.js` — select, don't build
- Resolve the focus to a `viewId`: no focus → `"system"`, `focus.kind === 'module'` → `"module:<focus.id>"`, else `"component:<focus.id>"`.


### 2. Retire superseded builders
- Remove `moduleGraph.js`, `clusterLayout.js`, `flatLayout.js`, `componentGraph.js`, and `frontend/src/hooks/graph/templates/*` (now computed in the render agent).
- `systemGraph.js`: already a thin consumer — keep or fold into `useGraphTransform`.
- **Keep**: node components (`CustomNode`, `ZoneGroupNode`, `ClusterGroupNode`, `ModuleSummaryNode`, `ModuleGroupNode`, `ModuleGhostNode`, `ZoneMoreNode`), `FlowGraph.jsx`, and the theme helpers in `common.js`.

### 3. Wire the view map through
- `AnalyseResponse.diagram.views` → `DiagramPage.jsx` → `DiagramExplorer.jsx` → `useGraphTransform`.

### 4. Progressive "+N more" reveal
- Backend precomputes the **full** module view (all primary + secondary components positioned).
- Keep the existing "+N more" / `expandedZones` interaction as a **client-side visibility toggle** over the already-positioned secondary nodes (show/hide; no reflow).
- *Decision:* accept whitespace when collapsed. Reflow-on-expand is a follow-up, not in scope.

## Acceptance criteria
- All three levels render from backend positions; mesh-type system view is stable across reloads.
- **Module view shows connecting lines between components** (the reported "floating" bug is fixed where edges exist).
- Component view shows caller/callee/child edges.
- "+N more" still reveals secondary components.
- `vite build` passes; no imports of `dagre`, `mermaid`, or the removed builders remain.

## Out of scope
- Any change to the node components' visual design.
- Reflow-on-expand layout.
