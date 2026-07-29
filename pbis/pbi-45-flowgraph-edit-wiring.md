# PBI 45 — Frontend: FlowGraph edit-mode wiring

**Batch:** 12 &nbsp;|&nbsp; **Depends on:** 41, 43, 44 &nbsp;|&nbsp; **Read `README.md` first.**
**Frontend changes are explicitly authorized for this PBI** (overrides the usual rule).

## Why
Turn the read-only canvas into an editor when `editMode` is on: seed from saved overlay, enable
drag/connect/select/delete, expose text/arrowhead/line tools, and brighten the grid — while keeping
today's read-only navigation untouched when `editMode` is off.

## Scope — `frontend/src/components/diagram/FlowGraph.jsx`
- **New props:** `editMode`, `overlay`, `graphKey`, and mutators from PBI 42
  (`onConnectEdge`, `onDeleteElements`, `onMoveNode`, `onSetEdgeMarker`, `onSetEdgeStyle`,
  `onAddText`, `onSetNodeLabel`).
- **Seed:** initialize nodes/edges from `applyEdits(externalNodes, externalEdges, overlay)` (PBI 41).
  Change the seeding `useEffect` to depend on **`graphKey`** (view switch) — not the raw
  node/edge arrays — so live edits are never clobbered mid-session. Keep the existing `fitView` there.
- **When `editMode`:** set `nodesDraggable`, `nodesConnectable`, `elementsSelectable`,
  `deleteKeyCode={['Backspace','Delete']}`; wire:
  - `onConnect` → build an edge (default `smoothstep`, `MarkerType.ArrowClosed`, neutral stroke), add
    to state and `onConnectEdge(edge)`.
  - `onNodesDelete` / `onEdgesDelete` → `onDeleteElements({nodeIds, edgeIds})` (React Flow removes
    from state; ignore attempts to delete backbone group nodes if needed).
  - `onNodeDragStop` → `onMoveNode(id, position)` (persist position; do **not** use `onNodesChange`).
  - `onSelectionChange` → track selected node/edge ids for the toolbar.
- **Add Text:** create a `type:'text'` node at viewport center (via `rfInstance.project` /
  `screenToFlowPosition`), inject its `onCommit` → `onSetNodeLabel`/text handler, add to state and
  `onAddText(node)`.
- **Toolbar actions:** render `<EditToolbar>` (PBI 44); arrowhead/line actions map over selected
  edges → update `markerEnd`/`markerStart` or `style.strokeDasharray` in state and call
  `onSetEdgeMarker`/`onSetEdgeStyle`.
- **Grid:** when `editMode`, switch `<Background>` to a brighter draw.io-style grid
  (e.g. `variant={BackgroundVariant.Lines}`, lighter color, larger gap); keep the current subtle dots
  in view mode.
- **Off path unchanged:** when `editMode` is false, behavior (drill/center on click) is exactly as
  today. Split helpers into `frontend/src/components/diagram/edit/` if the file would exceed 150 lines.

## Acceptance criteria
- Edit off: identical to current behavior.
- Edit on: nodes drag; dragging between handles creates an edge; selecting an edge + toolbar changes
  its arrowhead (none/open/filled) and solid/dashed; Delete/Backspace and the Delete button remove
  the selection; Add Text drops an editable box; the grid is visibly brighter.
- Each of the above invokes the matching mutator so the change persists (PBI 42) and re-appears on
  return to the view.

## Out of scope
- Inline relabel of existing component nodes (PBI 46) and page/explorer wiring (PBI 47).
