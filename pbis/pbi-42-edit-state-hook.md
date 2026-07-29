# PBI 42 — Frontend: diagram-edit state hook

**Batch:** 12 &nbsp;|&nbsp; **Depends on:** 40, 41 &nbsp;|&nbsp; **Read `README.md` first.**
**Frontend changes are explicitly authorized for this PBI** (overrides the usual rule).

## Why
A single place to own the `{ view_id: overlay }` map for a repo: load it once, expose the current
view's overlay + granular mutators to the canvas, and debounce-save to the backend. Keeps
`DiagramExplorer` / `FlowGraph` free of persistence concerns.

## Scope

### Hook — `frontend/src/hooks/useDiagramEdits.js` (new)
`useDiagramEdits(repo)` →
- Loads the map once via `getDiagramEdits(repo)` on mount / repo change; `loading`/`error` state in
  the spirit of `src/hooks/useAnalysis.js`. Holds the map in `useState`.
- `overlayFor(viewId)` → the overlay for a view (or an empty overlay).
- Mutators, each `(viewId, ...)` updating that view's overlay immutably then scheduling a save:
  `addEdge`, `deleteElements(viewId, {nodeIds, edgeIds})`, `setEdgeMarker`, `setEdgeStyle`,
  `moveNode`, `setNodeLabel`, `addTextNode`, `setTextNodeLabel`. Deleting an id that was locally
  added should remove it from `added_edges`/`text_nodes` rather than adding to `deleted_*`.
- A **debounced** `saveDiagramEdits(repo, map)` (e.g. ~600ms trailing) so rapid edits coalesce.

Keep ≤150 lines — if needed, factor the immutable overlay-reducer into
`frontend/src/hooks/graph/overlayReducer.js` and/or a tiny `debounce` util.

## Acceptance criteria
- On mount the hook fetches once and exposes the saved map; `overlayFor` returns per-view overlays.
- Each mutator updates the in-memory map correctly (verified via the UI in later PBIs) and results in
  exactly one PUT after the debounce window, containing the full updated map.
- Load failure surfaces via `error` and leaves an empty map (editing still works locally).

## Out of scope
- Rendering/interaction (PBIs 43–47). The hook is state-only.
