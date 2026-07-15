# F11 — Flow layout (geometry)

Depends on: F01 (contract); consumes F09/F10 output
Deliverable: render agent: `placement/flow_page_placer.py`, `placement/lane_packer.py`,
`placement/spine_router.py`
Replaces: the per-view placement paths for system/module/component views.

## Why

Deterministic geometry for the one-page FlowGraph. The render agent stays LLM-free
(as today). Shape is emergent from the data: a lane with no decisions IS a pipeline;
a route table IS a hub; nested decisions ARE a tree. No shape is ever selected.

## Spec

### Page composition

- Horizontal **swimlanes**, one per lane, stacked by `mass` descending. Lane header =
  `llm_title or name` at the left edge.
- Within a lane, flow runs **left → right**: entries at x=0 column; effects
  right-aligned to the lane's last column; steps/decisions/parallels in between at
  their topological depth (longest-path layering over the lane's DAG).

### The spine

Per entry, mark the **happy path**: at each decision follow the arm with the largest
reach (F06 data, carried in meta; ties → first by arm index). Set `is_spine=true` on
its edges. Spine nodes sit on the lane's vertical center line; spine edges render
bold. Non-spine arms leave the decision downward, their subflows stacked below in
arm-index order. `guarded` badges render as a small chip on the step (hover = the
guard's `label_source`), NOT as separate nodes — guards must not consume visual
bandwidth.

### Node treatment

- entry: rounded pill, method+path;
- step: rectangle, label + (folded_count ? `+N` chip);
- decision: diamond (branch/match/except) / trapezoid (table/route/polymorphic) —
  the question text inside, arm labels ON the edges;
- parallel: split bar (all out-edges leave together; reconverging edges join a bar);
- effect: icon per `EffectKind` + target text, flat-side against the lane's right edge;
- dynamic: dashed border + "runtime dispatch" subtitle. `except` arm edges dashed.

### Cross-lane stitches

`stitch` edges route in the gutter between lanes, orthogonal, entering the target
lane at its entry node. When lane A's effect stitches to lane B, the packer orders
lanes to minimize total gutter crossing distance (greedy adjacent-swap until stable —
deterministic, seeded by mass order).

### Determinism & sizing

Fixed grid: column width / row height constants in one config dataclass. Text
truncation with ellipsis at node width; full text to tooltip. Coordinates are pure
functions of the graph — byte-identical `RenderedView` across runs. Canvas size grows
with content; the FRONTEND scales to fit (F12) — the placer never drops content to
save space (that was F09's job).

## Non-goals

No force-directed layout, no dagre, no LLM, no interactivity (F12), no minimap logic.

## Acceptance

On CodeFlow: api lane on top (highest mass), its four stitch edges reaching each
agent lane without crossing through nodes; the tracer lane reads left→right
entry→steps→db+response effects; zero coordinate jitter across two runs (diff the
JSON); a synthetic 3-lane fixture with a 5-arm folded decision renders without
overlaps (assert pairwise node-rect disjointness).
