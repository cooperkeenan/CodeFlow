# PBI 43 — Frontend: editable text-box node

**Batch:** 12 &nbsp;|&nbsp; **Depends on:** — &nbsp;|&nbsp; **Read `README.md` first.**
**Frontend changes are explicitly authorized for this PBI** (overrides the usual rule).

## Why
Draw.io-style editing needs free-floating text boxes the user can place and type into. This is a new
React Flow node type; wiring it into the canvas/toolbar happens in PBIs 44–45.

## Scope

### Node — `frontend/src/components/diagram/nodes/TextNode.jsx` (new)
- Renders `data.text` as a draggable, selectable text box styled for the dark theme (reuse colors
  from `src/constants.js`; transparent/subtle background, thin border when selected).
- Double-click enters edit: an inline `<input>`/`contentEditable`; commit on blur / Enter calls
  `data.onCommit(id, text)` (Escape cancels). No handles required (or hidden handles), consistent
  with `CustomNode` handle styling.
- Presentational only — no store access; the commit callback and initial `text` come via `data`.
- ≤150 lines.

### Registration
Add `text: TextNode` to `NODE_TYPES` in `frontend/src/components/diagram/FlowGraph.jsx`.

## Acceptance criteria
- A node of `type: 'text'` renders its text; double-click makes it editable; committing raises
  `data.onCommit(id, newText)`; empty text still renders an editable placeholder box.
- Visually consistent with the existing dark canvas nodes.

## Out of scope
- Creating text nodes / persisting them (PBIs 44, 45). This PBI only defines + registers the type.
