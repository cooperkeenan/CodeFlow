# F12 — Frontend: the one-page view

Depends on: F01 (contract), F11 (geometry)
Deliverable: frontend: `src/pages/FlowPage.jsx`, `src/components/flow/*` (node
components per kind, edge component, legend, provenance popover)
Replaces: the drillable system/module/component navigation (view switcher, breadcrumb
drill, `ZoneMoreNode` expansion) — remove them and their routes.

NOTE: this feature explicitly authorizes frontend/ changes (CLAUDE.md requires the
task doc to say so — this is that statement; carry it into every PBI cut from this
feature).

## Why

The product decision: the whole codebase on one page, no drill-down. The frontend
becomes a single React Flow canvas that renders the FlowGraph verbatim — it must not
re-layout, re-rank, or hide anything the backend emitted.

## Spec

### Rendering

- Positions come from the render agent (as today — no dagre, no client layout).
  Fit-to-view on load; pan/zoom free; minimap on for graphs > 20 nodes.
- One custom node component per `NodeKind` matching F11's treatments; one custom
  edge honoring `kind`, `is_spine` (bold), `except`/dashed, `stitch` (gutter style),
  and rendering `llm_label or arm_label` as the edge label.
- `folded_count` renders as a static `+N` chip. It is NOT clickable — folding is
  final (one page). Tooltip lists the folded arm labels from `meta` if present.
- Badges: loop ⟳, recursive ⟲, guarded ⛨ (tooltip = guard source), dynamic ⚡.
- Legend (collapsible): node shapes, edge styles, badges, confidence styling —
  `inferred` edges render 60% opacity, `dynamic` dashed; the legend says why.

### Provenance popover

Click any node → popover with `one_liner`, backing component list, and `refs` as
`file:line` rows. Rows link to the repo blob URL when the repo metadata provides a
base URL; otherwise plain text. This is the trust anchor: every box on the page
points at real source.

### Page chrome

`page_title` as heading; lane titles rendered by the canvas (they arrive as
geometry from F11). Remove: view switcher, drill breadcrumbs, per-view diagram-type
chrome, and the depth/expansion controls. Keep: theme, repo picker, run status.

### API

One endpoint feeds the page: the rendered FlowGraph (geometry + labels). Delete the
per-view fetch hooks; `useGraphTransform` shrinks to a pure adapter
FlowGraph→ReactFlow props with zero business logic.

## Non-goals

No client-side filtering/search (future), no editing, no re-layout on resize beyond
fit-to-view scaling, no depth slider.

## Acceptance

Load CodeFlow's graph: whole pipeline visible on one screen at fit-to-view; hovering
the api→tracer stitch edge highlights both endpoints; clicking the except-decision
in the layout lane shows `service_step_planner.py:<line>`; no network request occurs
on any canvas interaction (everything client-side from one payload); removing the
old views leaves no dead routes (build passes, no unused imports).
