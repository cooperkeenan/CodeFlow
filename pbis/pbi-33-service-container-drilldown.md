# PBI 33 — Container drill-down for a folded service (layout + render)

**Batch:** 10 &nbsp;|&nbsp; **Depends on:** PBI 32 &nbsp;|&nbsp; **Read `README.md` first.**

## Why
When you drill into a service, you should see what it actually uses: the folded adapter/tool, the
service itself, and its helpers — grouped in a bordered container, with the upstream caller feeding in
(per the figma mockup: a "Call Graph Service" box containing `BuildCallGraphTool → CallGraphService →
CallGraphHelper`, with `TracerService →` entering from the left).

## Scope

### 1. Layout — `agents/layout_agent/services/_view_builder.py:build_component`
For a service that had members folded into it (from PBI 32's `meta["folded"]`), build a **grouped**
component template:
- a container group node for the service (reuse a `kind` like the `zoned` group nodes);
- inside it: the folded adapter(s), the service, and the service's helpers, with their internal edges;
- the upstream caller/orchestrator as an external node with one edge into the container.

### 2. Render — `agents/render_agent/placement/*`
Place the container + its members using the existing group/zoned placement machinery (the
`moduleGroup`/`zoneGroup`/`clusterGroup` pattern); position the external caller to the left feeding in.

### 3. Frontend
Render the container group with the existing group-node styling (reuse what `zoned` uses). **Frontend
edit authorized for this PBI.**

## Acceptance criteria
- Drilling into a service (e.g. `CallGraphService`) shows a bordered container holding its folded tool
  + the service + its helpers, with the caller (e.g. `TracerService`) feeding in — matching the mockup.
- Services with nothing folded fall back to the normal component view (no empty container).
- Determinism at temperature 0.

## Out of scope
- The contraction logic / which nodes get folded (PBI 32).
