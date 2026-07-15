# Decision-Flow Tracer — Feature Set

Authoritative spec for the tracer rework. Each numbered file is one feature, sized to
decompose into 1–4 PBIs. `docs/decision_flow_tracer.md` holds the rationale; where the
two disagree, **these files win**.

## Mission

One page. The whole codebase. Laid out the way a human holds it in their head:
entry points on the left, real decisions as labeled forks, effects (DB / HTTP / LLM /
response) on the right, services as swimlanes, cross-service calls stitched into one
continuous journey. No drill-down.

## Principles (apply to every feature)

1. **Static analysis owns structure; the LLM only names things.** No LLM call may add,
   remove, merge, or rewire a node or edge. Ever.
2. **Determinism**: same repo in, byte-identical FlowGraph out (labels excepted — the
   single LLM call is temperature 0 and keyed to ids, so only wording may vary).
   All iteration over sets/dicts is sorted; all ties break on `(file, line, name)`.
3. **Honesty**: what cannot be resolved statically is rendered as `dynamic`, never
   guessed. Every node carries `file:line` provenance back to real source.
4. **Graded confidence**: edges are `resolved` (proof), `inferred` (unique-name or
   callback heuristics), or `dynamic` (unresolvable). Filters and budgets prefer
   higher confidence; nothing silently drops lower.
5. **Decisions are dispatch sites, not if-statements**: branch, match, table, route,
   polymorphic, except-fallback, dynamic — one abstraction, seven detectors.

## Stage → feature map

| # | feature | pipeline stage | agent |
|---|---------|----------------|-------|
| 01 | flow-graph-models | shared contract | shared/ |
| 02 | project-indexer | 1 index | tracer |
| 03 | call-resolver | 2 resolve | tracer |
| 04 | dispatch-extraction | 3 dispatch sites | tracer |
| 05 | effect-detection | 3b effects | tracer |
| 06 | significance-filter | 4 filter + rank | tracer |
| 07 | flow-condensation | 5 FlowGraph | tracer |
| 08 | cross-service-stitching | 5b stitch lanes | tracer |
| 09 | one-page-budget | 6 budget | tracer |
| 10 | flow-labeling | 7 LLM labels | layout |
| 11 | flow-layout | 8 geometry | render |
| 12 | frontend-one-page | render | frontend |
| 13 | pipeline-cutover | integration + deletion | all |

## Dependency order

```
01 ──► 02 ──► 03 ──► 04 ──► 06 ──► 07 ──► 08 ──► 09 ──► 10 ──► 13
                     05 ──────────┘                11 ──► 12 ──┘
```

02→07 are strictly sequential. 05 needs only 02–03. 11–12 can start once 01 is merged
(they consume the FlowGraph contract) and finish against 09's output.

## Turning these into PBIs

- Respect `CLAUDE.md`: ≤150 lines/file, constructor injection, one class per file,
  type annotations everywhere, no unsolicited tests.
- Each feature lists **Acceptance** checks. They are part of the feature's scope —
  implementing the check (usually "run on CodeFlow itself and assert observations")
  is solicited work, not unsolicited testing.
- A PBI must not span two features. A feature may be split at the `##` section
  boundaries of its Spec.
- Features 02–09 are pure functions with no I/O beyond their inputs: no network, no
  LLM, no globals. This is what makes the pipeline snapshot-stable.

## Global acceptance (after 13)

Run the pipeline on CodeFlow itself:
- Lanes appear for `api` and the four agents; `frontend`/`shared` are backing detail,
  not lanes.
- The api→agent httpx calls are stitched into the agents' route entries (one
  continuous journey per user action).
- `ServiceStepPlanner.plan`'s try/except LLM-fallback surfaces as an except-decision;
  `raise ValueError("LLM did not return valid JSON")`-style guards do **not** surface
  as decisions.
- Running twice produces byte-identical FlowGraph JSON (ignoring LLM label strings).
