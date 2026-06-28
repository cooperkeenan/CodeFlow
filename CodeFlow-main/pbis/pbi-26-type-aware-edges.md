# PBI 26 — Type-aware edge construction in templates (layout)

**Batch:** 7 &nbsp;|&nbsp; **Depends on:** — &nbsp;|&nbsp; **Read `README.md` first.**

## Why
A `pipeline` view still reads as a hub: `component:TracerService` is `type: pipeline` with the nodes
ordered, but its **edges are the raw call edges** (`TracerService → FetchLayerFilesTool`,
`TracerService → BuildCallGraphTool`, … — a star), and `meta.order` is `None`. Edges are currently
**type-agnostic** — every template inherits the orchestrator's fan-out, so only node *positions*
change per type. A real template must own **edges that match its type**, not just its layout.

## Scope

### 1. Edge builder — `agents/layout_agent/services/_edge_builder.py` (new)
A per-type function producing the edges (and any node ordering) for a template. Keep ≤150 lines.
Contract:

| Type | Nodes | Edges |
|------|-------|-------|
| `pipeline` | `[caller(s), focus, step1…stepN]` in order | `caller→focus` (keep original edge_type), then a chain `focus→step1→step2→…→stepN`; **drop** the fan-out `focus→step_k` |
| `hierarchy` | focus + descendants | parent→child tree edges by depth (`focus→child`, `child→grandchild`) |
| `layered_tier` | nodes tagged by tier | downward cross-tier edges |
| `hub_and_spoke` | hub + spokes | `hub→spoke` (unchanged) |
| `mesh` / `dependency_graph` / `relationship` | involved nodes | raw spec edges among them (unchanged) |

### 2. Wire-in — `agents/layout_agent/services/_view_builder.py`
`build_component` and `_build_structural_module` call the edge builder instead of emitting raw spec
edges. For `pipeline`, order nodes `[callers, focus, ordered steps]` and set `meta["order"]`. For
`hierarchy`/`layered_tier`, set the meta the render placements already read (`depth_map` /
`tier_indices`). Other types keep current edges/meta.

### 3. Sequence order — `services/component_type_planner.py` + `prompts/component_type_prompt.py`
Batch 6 (PBI 25) was meant to return the ordered step list for sequential types but `meta.order` is
`None`. Make the planner return and the builder persist `order`. Fall back to a topological sort of
the type's edges when no order is provided.

## Acceptance criteria
- `component:TracerService` has edges
  `TracerClient→TracerService→FetchLayerFilesTool→BuildCallGraphTool→BuildEvidenceTool→SpecAssembler→GraphValidator→CorrectionPromptBuilder`,
  no star edges, and a populated `meta["order"]`.
- Hub / mesh / dependency_graph views are unchanged.
- Deterministic at temperature 0.

## Out of scope
- Render placement / edge styling (PBI 27).
