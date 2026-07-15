# F13 — Pipeline cutover & deletion

Depends on: all of F01–F12
Deliverable: rewired agents, deleted legacy machinery, self-run acceptance.

## Why

The new pipeline replaces, not augments. Keeping both paths alive doubles every
future change; git history is the rollback.

## Spec

### New pipeline wiring (agent responsibilities redefined)

```
profiler  (unchanged)      → RepoBlueprint (lanes/naming context only)
tracer    (stages 1–6+8+9) → budgeted FlowGraph          POST /trace
layout    (stage 7)        → FlowGraph + llm_* labels    POST /layout
render    (stage 8/F11)    → FlowGraph + geometry        POST /render
frontend  (F12)            → one page
```

- `TracerService` becomes: fetch → persist → index (F02) → resolve (F03) →
  dispatch+effects (F04/F05) → filter (F06) → condense (F07) → stitch (F08) →
  budget (F09) → return FlowGraph. All stages constructor-injected, each ≤150-line
  service, pure between fetch and return.
- `TracerResponse` carries `flow_graph: FlowGraph`. The api gateway threads it
  through layout → render unchanged in shape.
- Layout agent keeps ONLY: F10 labeler + validator (+ its client plumbing).
- Render agent keeps ONLY: F11 placement (+ routers/plumbing).

### Delete (git rm, plus their models/prompts/DI wiring and dead config)

tracer: `services/evidence/call_graph_service.py` (jarviscg dep from requirements
too), `services/evidence/ast_service.py`, `services/evidence/http_visitor.py`,
`services/evidence/evidence_service.py`, all of `services/tracing/` (chunk tracer,
breadcrumbs, partitioner, correction builder), `services/assembly/` (merger,
assembler, validator, recovery, placer), `LineRangeEnricher` (refs live on nodes
now).
layout: `service_step_planner.py`, `service_step_validator.py`,
`service_step_prompt.py`, `template_planner.py` + type-choice prompts,
`view_planner.py`, view builders, hierarchy/archetype/cluster helpers not used by
F10, `importance_scorer.py` (superseded by F06).
frontend: per F12.
Keep: `FileFetchService`, `SourcePersistService`, profiler agent, stores, gateway.
`DiagramSpec`/`DiagramTemplate` stay only if the profiler still emits them; strip
diagram-side usage.

After deletion run an unused-import/dead-file sweep across all four agents.

### Self-run acceptance (the feature's definition of done)

A script (`scripts/selfrun.sh` or api call against local compose) that runs the full
pipeline on CodeFlow's own checkout and writes the final FlowGraph JSON + rendered
page. Assert programmatically:

1. lanes = {api, profiler, tracer, layout, render agents}; shared/frontend absent;
2. ≥4 stitch edges api→agent entries;
3. an `except`-kind decision exists in the layout lane (LLM-fallback pattern);
4. zero decisions whose selector matches `not |is None|!= None` (guards filtered);
5. every node has ≥1 SourceRef resolving to a real file:line in the checkout;
6. two consecutive runs: FlowGraph JSON byte-identical ignoring `llm_*`/titles;
7. node count ≤ budget invariant (F09).

Update `PROMPT.md`'s "Current Status" section to describe the new pipeline (delete
the hierarchy-aware three-view description). Update README pipeline diagram.

## Non-goals

No backward-compat flag, no dual emission, no migration of stored diagrams (rerun
repos instead).

## Acceptance

The seven assertions above pass; `docker-compose up` + frontend shows CodeFlow on
one page; `grep -r jarviscg` returns nothing; mypy clean; no file exceeds 150 lines.
