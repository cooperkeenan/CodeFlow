# PBI 46 — Frontend: inline label editing on existing nodes

**Batch:** 12 &nbsp;|&nbsp; **Depends on:** 45 &nbsp;|&nbsp; **Read `README.md` first.**
**Frontend changes are explicitly authorized for this PBI** (overrides the usual rule).

## Why
"Change existing text" must also cover the real diagram nodes, not just new text boxes. In edit mode,
double-clicking a component node lets the user rename it, persisted as a `node_overrides.label`.

## Scope — `frontend/src/components/diagram/CustomNode.jsx`
- When `data.editMode` is true, double-click swaps the label for an inline `<input>` seeded with the
  current label; commit on blur / Enter calls `data.onLabelCommit(id, text)` (Escape cancels).
- FlowGraph (PBI 45) injects `editMode` and `onLabelCommit` into each editable node's `data`, wiring
  `onLabelCommit` → `setNodes` + `onSetNodeLabel` (PBI 42).
- View-mode behavior (single-click drill/expand, description toggle) is unchanged; double-click does
  nothing when `editMode` is false. Keep the change minimal; stay ≤150 lines (extract a tiny
  `InlineLabel` helper if needed).

## Acceptance criteria
- Edit on: double-clicking a component node makes its label editable; committing updates the node and
  persists via `node_overrides.label`; the new label survives leaving and re-entering the view.
- Edit off: node click behavior is exactly as today; no inline editor appears.

## Out of scope
- Editing edge labels (covered by edge overrides in PBI 45); page wiring (PBI 47).
