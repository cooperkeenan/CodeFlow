# PBI 47 — Frontend: wire edit mode through the page

**Batch:** 12 &nbsp;|&nbsp; **Depends on:** 42, 45, 46 &nbsp;|&nbsp; **Read `README.md` first.**
**Frontend changes are explicitly authorized for this PBI** (overrides the usual rule).

## Why
Final integration: the header **Edit** toggle, and threading edit state + per-view overlay + mutators
from `useDiagramEdits` into `FlowGraph` so the whole feature works end to end.

## Scope

### 1. Header toggle — `frontend/src/pages/DiagramPage.jsx`
Add an **Edit** toggle button next to the existing `</> code view` button, mirroring its styling and
`codeViewMode` on/off pattern (lit green when active). Lift `editMode` state here; pass it into
`DiagramExplorer`.

### 2. Explorer wiring — `frontend/src/components/diagram/DiagramExplorer.jsx`
- Instantiate `useDiagramEdits(repo)` (PBI 42).
- Compute the current `viewId` (same value as `graphKey`: `system` | `module:<id>` | `component:<id>`).
- Pass to `FlowGraph`: `editMode`, `graphKey`, `overlay={overlayFor(viewId)}`, and the mutators bound
  to the current `viewId` (so `FlowGraph` calls them without knowing the view).
- In `handleNodeClick`, when `editMode` is true, **do not** drill/expand or open panels — leave
  selection/editing to the canvas. All existing view-mode behavior stays for `editMode` false.

## Acceptance criteria
- The Edit toggle turns the canvas into edit mode (brighter grid + toolbar) and back; view-mode
  behavior (drill, code view, centering) is unchanged when off.
- Full flow works: draw/delete lines, change arrowheads + line style, add text boxes, rename nodes,
  drag nodes. Edits persist across refresh and across drilling into/out of views (per-view overlays).
- Re-analysing a repo does not crash on stale overlays (unknown ids ignored — PBI 41).

## Out of scope
- Image/PNG export (deferred). Reflecting the current drill-down in the URL (not required).
