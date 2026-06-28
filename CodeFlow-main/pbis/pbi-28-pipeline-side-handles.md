# PBI 28 — Pipeline edges route into the sides (frontend)

**Batch:** 8 &nbsp;|&nbsp; **Depends on:** — &nbsp;|&nbsp; **Read `README.md` first.**

## Why
A horizontal pipeline view chains correctly now, but React Flow connects the nodes through their
**top/bottom handles**, so the arrows droop vertically and look messy. For a left→right pipeline the
arrows should enter the **sides** (right edge → left edge).

> **Frontend edit authorized for this PBI.**

## Scope
- In the frontend graph transform (`frontend/src/hooks/useGraphTransform.js` / `graph/common.js`
  `toRFNode`/`toRFEdge`), when the **view type is `pipeline`** (or an edge's `edge_type` is
  `sequence`), set each node's `sourcePosition: 'right'` and `targetPosition: 'left'` and render the
  connecting edges as `smoothstep`.
- Ensure the custom node component exposes left/right handles (add them if it only has top/bottom).
- Leave non-pipeline views (hub_and_spoke radial, zoned grid, mesh, etc.) exactly as they are.

## Acceptance criteria
- A pipeline view's arrows run horizontally, side-to-side, with no vertical drooping.
- Other view types are visually unchanged.

## Out of scope
- The system-view ordering/edges (PBI 29). Any backend changes.
