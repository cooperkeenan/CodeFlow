# F07 — Flow condensation (FlowGraph construction)

Depends on: F04, F05, F06
Deliverable: `agents/tracer_agent/services/analysis/flow_condenser.py`
(+ `function_summarizer.py`, `entry_finder.py`)

## Why

Turns facts (call graph + decisions + effects) into the page's shape: the FlowGraph.
Formally: the **projection of the interprocedural flow onto anchor nodes** — every
path between anchors that touches no other anchor becomes one Step.

## Spec

### Anchors

`entries ∪ decisions (F06) ∪ parallel sites ∪ effects (F05)`.

**Entry detection** (in `entry_finder.py`, extensible detector list):
- every arm of a `route` site (method+path = the entry's label);
- `if __name__ == "__main__":` blocks and `[project.scripts]` console entries;
- `<module>` functions executed as scripts (uvicorn targets from Dockerfiles/compose
  are out of scope v1 — the FastAPI app object itself is the entry).

**Parallel sites**: `asyncio.gather(...)`, `asyncio.TaskGroup`, `create_task` — a
`parallel` node whose out-edges (kind `parallel`) lead to each awaited callee's flow.
This is AND fan-out; never confuse with decisions (XOR).

### Function summaries (the core algorithm)

Bottom-up over the call graph's SCC condensation (recursive SCCs collapse to one
summary with a `recursive` badge):

```
summarize(f) -> Summary:            # memoized; Summary is a mini-DAG
  nodes: anchors lexically in f (decision/parallel/effect) in AST order,
         wired by f's control structure:
           - inside a decision arm  -> reached via that arm's edge
           - guarded_step guards    -> "guarded" badge on the absorbing segment
           - noise sites            -> dissolved (arms inlined sequentially)
  calls: for each CallSite (in AST order) splice the callee's Summary:
           - resolved/inferred      -> splice (shared: same node ids => convergence)
           - in_loop                -> "loop" badge on the spliced segment's entry
           - dynamic (no targets)   -> dynamic pseudo-anchor node
  segments between anchors collapse into Step stubs carrying backing fqns (ordered,
  deduped) and merged SourceRefs
```

Splicing is context-insensitive: a function summarized once keeps the same node ids
everywhere it is called, so shared subflows **converge** in the DAG instead of
duplicating (diamonds are natural; the graph is a DAG after SCC collapse).

### Assembly

For each entry, instantiate its handler's summary; prepend the Entry node. Consecutive
Step stubs merge. Steps synthesize labels from their dominant backing component
(highest reach) — the deterministic `label` of F01. Node/edge ids per F01's scheme.

### Lanes

One lane per **runnable service**: a module subtree owning ≥1 entry (reuse the
blueprint's `is_service` modules where available; else group entries by top-level
package). `lane.mass` = Σ score of its decisions + Σ arm count of its route sites.
Everything else (`shared/`) appears only as backing detail inside steps.

## Non-goals

No budget (F09), no stitching (F08), no labels (F10), no geometry (F11). Depth of
step granularity is NOT configurable — the budget alone controls the page.

## Acceptance

On CodeFlow: lane per agent + api; `POST /trace` entry flows
Entry → step(fetch+persist) → … → effects(db, response) with the
`ServiceStepPlanner`-style except-decisions appearing as forks in the layout lane;
`ViewPlanner.plan`'s awaited sub-planner sequence appears as sequential steps (no fake
decision); byte-identical output across two runs.
