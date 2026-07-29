# PBI 41 — Frontend: overlay merge helper

**Batch:** 12 &nbsp;|&nbsp; **Depends on:** — &nbsp;|&nbsp; **Read `README.md` first.**
**Frontend changes are explicitly authorized for this PBI** (overrides the usual rule).

## Why
User edits are stored as a compact **per-view overlay diff** applied on top of the backend-computed
view. This PBI is the single pure function that applies an overlay to base nodes/edges, reused by the
canvas seed (PBI 45) and anywhere edits are rendered. Keeping it pure and id-tolerant means a later
re-analyse (different node ids) degrades gracefully — unknown ids are simply skipped.

## Scope

### Overlay shape (canonical — used across PBIs 41, 42, 45)
```
ViewOverlay {
  deleted_edge_ids: string[]
  deleted_node_ids: string[]
  added_edges:   RFEdgeJSON[]     // {id, source, target, sourceHandle?, targetHandle?, markerEnd, markerStart?, style?, label?}
  edge_overrides: { [edgeId]: { markerEnd?, markerStart?, style?, label? } }
  node_overrides: { [nodeId]: { label?, position? } }
  text_nodes:    RFNodeJSON[]     // {id, type:'text', position, data:{text}, width?, height?, style?}
}
```

### Helper — `frontend/src/hooks/graph/applyEdits.js` (new)
```js
export function applyEdits(baseNodes, baseEdges, overlay) -> { nodes, edges }
```
- Returns `{ nodes: baseNodes, edges: baseEdges }` unchanged when `overlay` is falsy/empty.
- Drop nodes/edges whose id is in `deleted_node_ids` / `deleted_edge_ids`.
- Apply `node_overrides`: set `data.label` and/or `position` on the matching base node (skip unknown
  ids). Apply `edge_overrides`: shallow-merge `markerEnd`/`markerStart`/`style`/`label` onto the
  matching base edge.
- Append `added_edges` (dedupe by id against base) and `text_nodes`.
- Reuse `MarkerType` from `reactflow` when normalizing marker values. Pure, no React, ≤150 lines.

## Acceptance criteria
- Empty/undefined overlay is a no-op passthrough.
- Deleted ids are removed; label/position/marker/style overrides are applied to the right elements;
  added edges and text nodes appear; unknown ids in overrides/deletes are ignored without throwing.

## Out of scope
- Persisting/loading (PBIs 40, 42) and rendering wiring (PBI 45).
