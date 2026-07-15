# Decision-Flow Tracer — Design

Replaces the current tracer pipeline. Goal: traverse a codebase, find every point where
control genuinely diverges, and lay the whole system out on **one page** the way a human
holds it in their head — entry points on the left, decisions as labeled forks, effects
(DB, HTTP, LLM, response) on the right. No drill-down.

> **v2 note — authoritative spec lives in `features/`.** A second review pass found
> gaps in this document; the corrected, implementable spec is `features/01`–`13`.
> The material changes:
> 1. **XOR vs AND**: `asyncio.gather`/parallel fan-out is a new `parallel` node kind —
>    do-all fan-out must never render as a decision (F01, F07).
> 2. **Guard reclassification**: an arm that terminates (raises/returns) with reach ≤ 2
>    is a *guard* even when it calls a distinct component (alert/notify arms); sites
>    with one live arm become a `guarded` badge on a step, not a decision (F06).
> 3. **Distinctness defined + utility damping**: arms are distinct iff neither reach
>    set is a subset of the other, computed after excluding high fan-in utility
>    components (F06).
> 4. **Single-impl polymorphism is indirection, not a decision** — ≥2 concrete
>    implementations required (F03/F04).
> 5. **Graded confidence** (`resolved`/`inferred`/`dynamic`) with composition-root
>    binding and unique-name inference, so untyped codebases degrade gracefully
>    instead of going dark (F03).
> 6. **Cross-service stitching** (F08): outbound HTTP effects match route entries in
>    other lanes — one continuous journey across services on the single page.
> 7. **No CFG/post-dominators needed**: arms, terminality, and reconvergence read
>    directly off the AST (F04).
> 8. **jarviscg fully retired** (was "optional cross-check") (F03, F13).

---

## 1. Why the current tracer is structurally wrong

The current pipeline asks an LLM to *derive* structure and uses static analysis only as a
hint. That is backwards, and it shows in four specific places:

1. **Class-level collapse.** `call_graph_service._to_serialisable` reduces jarviscg's
   function-level graph to class→class edges via an "any uppercase segment" heuristic.
   Function identity — where flows and decisions actually live — is destroyed at the
   first stage and never recoverable downstream. Module-level functions, `main()`s, and
   same-named classes in different packages are all mangled.
2. **Flat call extraction.** `ast_service._extract_calls` walks the whole tree and emits
   bare callee names. Which function a call lives in, which branch arm it sits under,
   whether it's in a loop or an `except` — all discarded.
3. **LLM-derived structure.** `TreeTraversalPartitioner` chunks the class graph, then
   `ChunkTracer` (Haiku, breadcrumbs, correction loop, merger) asks the LLM to guess
   components and edges from signatures. The structure the LLM is guessing is exactly
   what static analysis can compute deterministically. The chunk boundaries, breadcrumb
   summaries, and merge step each add loss and nondeterminism; `GraphValidator` and
   `EdgeRecovery` then try to patch the result back toward the facts.
4. **Wrong entry-point model.** "No incoming edges" as root detection misses framework
   entry points entirely — in a FastAPI codebase the routers *are* the entry points, and
   nothing calls them statically.

The fix is to invert the division of labor: **static analysis owns structure completely;
the LLM only names things.**

---

## 2. Core abstraction: the dispatch site

"If statements" were only ever an example. The unit is a **dispatch site**: any point
where one caller may invoke one of N alternatives. Every form of divergence in Python
reduces to this:

| kind          | source of divergence                          | arms come from                          |
|---------------|-----------------------------------------------|-----------------------------------------|
| `branch`      | `if / elif / else`, ternary, `and`/`or` calls | CFG arms of the statement                |
| `match`       | `match / case`                                | case arms                                |
| `table`       | dict-of-callables / registry lookup + call    | the dict's key→value entries             |
| `route`       | framework route tables (FastAPI decorators)   | one arm per registered route             |
| `polymorphic` | call through a base-type annotation           | overriding implementations               |
| `except`      | `try / except` with a fallback path           | try arm + each except arm                |
| `dynamic`     | `getattr(obj, f"...")`, exec-time lookup      | **unresolvable — rendered honestly**     |

Note what this buys us: the better a codebase follows Open/Closed (this repo's own
rules), the more its decisions live in tables, routes, and polymorphism rather than `if`
ladders. A branch-only detector works worst on the best codebases. A dispatch-site
detector treats all of these as the same thing.

A `DispatchSite` record:

```
DispatchSite:
    id: str                      # stable: "{owner_fqn}:{line}"
    owner: FunctionFqn
    kind: branch|match|table|route|polymorphic|except|dynamic
    selector_source: str         # the condition/key/type expression, verbatim
    selector_provenance: entry|param|internal
    arms: list[Arm]

Arm:
    label_source: str            # "== 'cat'", case pattern, dict key, route path, class name
    direct_callees: list[FunctionFqn]
    terminal: returns|raises|continues
```

---

## 3. The pipeline

Eight stages. Stages 1–6 are pure functions of the source tree — same repo, same output,
byte for byte. Stage 7 is the only LLM call. Stage 8 is deterministic layout.

### Stage 1 — Index
Parse every file once (`ast`). Build a project symbol table: module fqn → classes,
functions, methods; per-module import bindings (alias → symbol). Per function: qualified
name, params with annotations, return annotation, source span. This replaces
`extract_signatures` / `build_import_graph` and their uppercase heuristics.

### Stage 2 — Resolve (function-level call graph with call-site context)
For every call expression, resolve the target through a layered resolver:

a. bare name → local scope, then import bindings;
b. `self.x()` / `cls.x()` → own class, then MRO;
c. `self._dep.x()` where `_dep` was assigned from an annotated `__init__` param →
   the annotation's type (constructor injection makes this the workhorse — DI plus
   mandatory annotations means attribute calls resolve statically);
d. annotation is an abstract/base type with multiple concrete overriders → resolve to
   **all** implementations and record a `polymorphic` dispatch site;
e. otherwise → `dynamic`: recorded and counted, never guessed.

Every resolved call is a `CallSite`: caller fqn, target(s), line, and its **control
context** — the stack of enclosing control constructs (dispatch-site id + arm index),
loop flag, try/except arm. This context is the single most important thing the old
pipeline threw away.

jarviscg is retired from the primary path (it cannot supply call-site context). Its raw
function-level output may optionally be kept as a cross-check: edges found by both
resolvers are `confirmed`, mirroring today's intersection idea one level down.

### Stage 3 — Extract dispatch sites
Per function, a small CFG over the statement list yields `branch`/`match`/`except`
sites with per-arm direct callees. Module/class-level scans yield `table` sites
(dict literals whose values are callables/classes, joined to their lookup-and-call
sites) and `route` sites (one synthetic dispatch site per `APIRouter`/app, one arm per
route decorator — the richest and cheapest decision data in a FastAPI codebase).
`polymorphic` sites come from stage 2d.

### Stage 4 — Significance filter (the `!= null` vs `== "cat"` problem, solved statically)
For each arm, compute its **reach set**: project components transitively callable from
the arm's callees (bounded closure over the stage-2 graph). Then:

- **Divergence test (the gate):** a site survives iff **≥ 2 arms have non-empty,
  pairwise-distinct reach sets.** A null-guard fails automatically — its guard arm
  raises or returns early and reaches nothing. A router passes automatically — each arm
  reaches a different handler. No semantic judgment involved.
- **Score (the ranking):** among survivors,
  `score = w_r · |union of reach sets| + w_p · provenance + w_d · non-reconvergence`
  where *provenance* is 2 if the selector reads entry-point data (request param, CLI
  arg — traced as "tests a parameter of the function, or an attribute of one"), 1 for
  other params, 0 for internal state; and *non-reconvergence* is whether the arms ever
  rejoin within the owner function (immediate post-dominator distance, cheap on a
  per-function CFG). Weights are constants; ties break on `(owner, line)`.

Output: a total, stable order over all real decisions in the codebase.

### Stage 5 — Flow condensation
Entry points are found structurally: route tables, `if __name__ == "__main__"`, console
scripts, scheduled/CLI mains — not "no incoming edges". From each entry point, walk the
resolved call graph and **contract every maximal chain that contains no surviving
dispatch site into a single Step node** (carrying its backing components and spans).

The result is the **FlowGraph** — the decision skeleton:

- **Entry** nodes (route, main, CLI…)
- **Step** nodes (condensed linear segments; "the plumbing", one box)
- **Decision** nodes (surviving dispatch sites; outgoing edges carry arm labels)
- **Effect** nodes (I/O boundaries detected statically: outbound HTTP, DB, LLM calls,
  file writes, the response itself — `http_visitor` generalizes into an EffectVisitor)

It is a DAG with convergence (shared components render once), not a strict tree. Loops
become a "for each X" badge on the step, never a cycle on the page.

### Stage 6 — One-page budget
A node budget **B** (~35) replaces drill-down. Decisions are admitted in stage-4 score
order; below the cut, a decision's arms merge back into their containing step and the
graph is re-condensed. Small repos show every decision; large repos show the top ones —
but always the *same* ones, at every run. The old shape question disappears: zero
surviving decisions ⇒ the page **is** a pipeline; one dominant fan-out ⇒ a hub; nested
divergence ⇒ a tree. Shape is emergent, never chosen.

### Stage 7 — LLM labeling (the only interpretive step)
One call (temperature 0). Input: the skeleton — per decision its selector source and arm
sources; per step its component names, docstrings, spans; per effect its target. Output
schema: `{node_id: {label, one_liner}}` and `{(site_id, arm_index): arm_label}` —
"CPT question" / "MRF data", "Parse & validate request". The validator (pattern of
`ServiceStepValidator`) accepts only labels keyed to ids it issued. The LLM cannot add,
remove, merge, or rewire anything — hallucination is impossible by construction, and
structure is identical run-to-run; only wording can vary.

Fallback when the LLM call fails: render with source-derived labels (selector text,
top component name). The page is uglier, never wrong.

### Stage 8 — Layout (one page, deterministic)
Left→right: entries on the left edge, effects on the right. Multiple entry points get
swimlanes that converge on shared steps. At each decision, the **spine** continues with
the arm whose reach set is largest (the happy path, bold); guard and fallback arms exit
downward as thin edges. `except`-fallback arms render as dashed. `dynamic` sites render
as an explicit "dynamic dispatch (N candidates unknown)" fan — honest, not guessed.
Every node keeps `file:line` provenance; clicking shows the real selector source.

---

## 4. What this replaces

| dies | replaced by |
|------|-------------|
| `ChunkTracer`, `BreadcrumbBuilder`, `ChunkContextBuilder`, `CorrectionPromptBuilder`, `RawMerger`, `TreeTraversalPartitioner` | nothing — structure is no longer LLM-derived |
| `CallGraphService` class-collapse | stage-2 resolver (function-level, call-site context) |
| `AstService` flat extraction | stage-1 indexer + stage-3 visitors (`HttpCallVisitor` is the in-repo precedent for the visitor style) |
| `GraphValidator`/`EdgeRecovery` patch-up | not needed on the facts path; the only validator left guards LLM labels |
| service-step LLM planning + per-view diagram-type choice | FlowGraph + emergent shape |
| drillable system/module/component views | one budgeted page |

`FileFetchService`, `SourcePersistService`, and the render agent's placement machinery
survive; the frontend consumes one FlowGraph and needs labeled edges (a `label` field on
`TemplateEdge` — it has none today) and the four node kinds.

## 5. Known limits (rendered honestly, not papered over)

- **Pure runtime dispatch** (`getattr` with computed names, plugin loading): detected,
  arity unknown, shown as a dynamic-dispatch node. Never guessed.
- **Event-driven flow** (pub/sub, queues): the crossroad lives in a broker at runtime.
  Publishers and subscribers appear as effects/entries with an `event` edge; the design
  does not fabricate a decision that isn't in the code.
- **Huge fan-outs** (30-arm command dispatch): a real decision with unreadable arity —
  keep the top arms by reach-set size, fold the tail into one "+N other commands" arm.
- **Decorators/middleware**: framework-known ones (FastAPI `Depends`) are resolved as
  calls; unknown decorators pass through transparently.
- **Generalisation**: stages 4–8 are language-agnostic given a per-language front end
  (index + resolve + dispatch extraction). The Python front end leans on this codebase's
  own disciplines (annotations, DI) and degrades to `dynamic` where they're absent.

## 6. Determinism as the testing story

Stages 1–6 are pure: fixture repo in, FlowGraph out, snapshot-comparable byte-for-byte.
The retired evaluation harness scored one slice (modules/edges/entry recall); the
replacement, when wanted, is a handful of fixture repos with committed expected
FlowGraphs — a plain snapshot test, no scoring framework needed.

## 7. Build order

1. **Indexer + resolver** (stages 1–2) — the substrate everything else stands on.
2. **Dispatch extraction + divergence filter** (stages 3–4) — run it on CodeFlow itself;
   the route tables, `ViewPlanner`'s classifier fan-out, and the planner `try/except`
   fallbacks should surface, and every null-guard should not. That single check
   validates the whole idea before any rendering work.
3. **Condensation + budget** (stages 5–6) — FlowGraph model shared with layout.
4. **Labeling + validator** (stage 7).
5. **One-page layout + frontend** (stage 8): labeled edges, four node kinds, swimlanes.
