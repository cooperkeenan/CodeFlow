# PBI 27 — Render honors per-type meta + distinguishes flow edges

**Batch:** 7 &nbsp;|&nbsp; **Depends on:** PBI 26 &nbsp;|&nbsp; **Read `README.md` first.**

## Why
`placement_service._build_edges` passes `template.edges` through 1:1 and placements only position
nodes — so the new type-aware edges (PBI 26) must be drawn, and synthesized **sequence** edges should
be visually distinct from literal `call`/`http` edges so a derived "flow" arrow is not mistaken for a
real call.

## Scope

### 1. Honor the new meta/order — `agents/render_agent/services/placement_service.py` + placements
Verify each placement consumes what PBI 26 now produces: `component_pipeline` reads the new node order
(head-of-chain), `component_hierarchy` reads `depth_map`, `component_layered_tier` reads
`tier_indices`; the structural-module placements likewise. Adjust only where a placement ignores them.

### 2. Distinguish flow edges
Style synthesized chain/tree edges differently from literal calls — either a dedicated `sequence`
edge_type (add to `EdgeType` in `shared/models/diagram_spec.py` if taken this route) or a dashed
style + label. Touches `_build_edges` and the frontend edge styling helper
`frontend/src/hooks/graph/common.js` (`toRFEdge`). **Frontend edit authorized for this PBI.**

## Acceptance criteria
- A pipeline view renders as a left-to-right chain whose connections stay a chain when nodes are
  dragged; sequence edges are visually distinct from `call`/`http`.
- `hierarchy` / `layered_tier` views render with their correct edges; `hub_and_spoke` / `mesh` /
  `dependency_graph` and the system view are unchanged.

## Out of scope
- Building the edges themselves (PBI 26).
