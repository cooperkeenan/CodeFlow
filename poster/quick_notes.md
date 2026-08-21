# Quick notes

Cue card for standing at the poster.

## The tracer stages, one line each

| # | Stage | One line |
|---|---|---|
| 1 | **Index** | Parse every file into a symbol table — every function, class, parameter and line span. |
| 2 | **Resolve** | Build the call graph: who calls whom, and which branch arm each call sits under. |
| 3 | **Extract** | Find every candidate fork — if, match, except, table, route, polymorphic, dynamic. |
| 4 | **Effects** | Mark the calls that touch the outside world: db, http, llm, file, queue, email, response. |
| 5 | **Score** | Compute what each arm reaches and rank every fork on the four-term significance score. |
| 6 | **Judge** | The model reads the ranked forks and says decision / guard / noise, and writes the human question. |
| 7 | **Condense** | Turn the survivors into a graph of entries, decisions, effects and outcomes. |
| 8 | **Stitch** | Match outbound HTTP calls to the routes that serve them, so cross-service journeys join up. |
| 9 | **Budget** | Demote low-ranked nodes a level deeper so the page opens at ~15 nodes. Nothing is deleted. |
| 10 | **Name** | The model writes the label on each node, keyed to ids the pipeline already issued. |

Nine deterministic, one model-driven — that's the whole argument.

## Why is Judge a different colour?

**Amber = the model. White = deterministic. It's the only amber box on the diagram, and
that's the point.**

The colour is doing an argument, not decoration. `figures/fig1_architecture.py` sets
`AMBER_STAGE = "Judge"` and paints every other stage white, so a visitor can see at a glance
that seven of eight stages are pure functions of the source tree and exactly one talks to
Anthropic. Same reason the "model calls" arrow points only at that box.

If someone asks *"isn't this just ChatGPT for code?"*, point at the amber box:

> Everything white is static analysis. The model only reaches the amber stage, and by then
> the forks already exist — it's choosing from a list, not drawing anything. It cannot add a
> node, remove one, or draw an edge.

(Naming is also model-driven but sits after the render boundary, so it isn't a stage box in
Figure 1. If pressed: the model judges and names, nothing else.)

## How is layout handled now?

**The layout agent is no longer called.** `AnalysisService` still constructs a `LayoutClient`
and `layout.json` is still written, but it's a verbatim copy of the tracer's `flow_graph` —
the gateway goes tracer → render directly. The layout agent was a V1 artefact that had an LLM
enrich modules with tier/role labels; that job moved inside the tracer as `FlowNaming`, where
it is constrained to ids the pipeline issued.

**Geometry is computed deterministically by the render agent** —
`agents/render_agent/placement/`:

- `SpineRouter` picks the main path through the graph — the trunk everything else hangs off.
- `LanePacker` orders the swimlanes and packs nodes within them.
- `TreeLayout` places the containment tree; `flow_grid_config.py` holds the spacing constants.
- `HiddenEmitter` emits the collapsed `+N` children so expansion is instant.
- Only `level == 0` nodes are placed initially — that's the ~15-node opening page.

The frontend is a thin renderer: React Flow draws boxes at positions the backend supplied.
**No dagre, no Mermaid, no auto-layout library.** That's what makes "0 overlapping boxes" an
invariant that can be asserted rather than eyeballed — same input, same pixels, every run.
