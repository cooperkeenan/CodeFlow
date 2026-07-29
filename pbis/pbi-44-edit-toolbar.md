# PBI 44 — Frontend: edit toolbar ribbon

**Batch:** 12 &nbsp;|&nbsp; **Depends on:** — &nbsp;|&nbsp; **Read `README.md` first.**
**Frontend changes are explicitly authorized for this PBI** (overrides the usual rule).

## Why
The draw.io-style ribbon that appears at the top of the canvas in edit mode. Pure presentational
component; FlowGraph (PBI 45) supplies the callbacks and current selection/active-tool.

## Scope

### Component — `frontend/src/components/diagram/edit/EditToolbar.jsx` (new)
- Rendered as a React Flow `<Panel position="top-center">` (import `Panel` from `reactflow`).
- Tool group: **Select**, **Add Text** (highlight the active tool), **Delete** (calls
  `onDelete`; disabled when nothing selected).
- Edge-styling group, enabled only when ≥1 edge is selected:
  - **Arrowhead**: None / Open / Filled → `onSetArrowhead('none'|'open'|'closed')`.
  - **Line**: Solid / Dashed → `onSetLineStyle('solid'|'dashed')`.
- Props: `activeTool`, `hasSelection`, `hasEdgeSelection`, `onSelectTool`, `onAddText`, `onDelete`,
  `onSetArrowhead`, `onSetLineStyle`. Use MUI icons (already a dependency) + dark styling matching the
  header pill buttons in `DiagramPage.jsx`. No store/React Flow state access. ≤150 lines.

## Acceptance criteria
- Buttons render in a top-center ribbon; the active tool is visually indicated; edge-only controls
  are disabled without an edge selection; every button invokes its callback with the documented args.

## Out of scope
- Wiring callbacks to real behavior (PBI 45). Toolbar only emits intent.
