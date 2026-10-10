# CodeFlow — Architecture

## What This Is
CodeFlow generates a **decision diagram** from a Python codebase. It finds every point where the
code branches, has an LLM judge which of those are decisions a human would actually put on a mental
model of the system, and renders them as a tree with `file:line` provenance on every node.

The governing idea: **static analysis owns structure; the LLM judges significance and writes
labels.** The LLM may never add, remove, merge or rewire a node or edge.

## Architecture

Four deployable services plus an on-demand explain agent and a frontend:

- **Gateway** (`api/`, package `gateway`, 8000) — orchestrates the pipeline, serves the UI's HTTP
  API, persists results.
- **Profiler agent** (`agents/profiler_agent/`, package `profiler`, 8002) — repo module/zone
  skeleton → `RepoBlueprint`. The tracer consumes it to decide which directories to fetch.
- **Tracer agent** (`agents/tracer_agent/`, package `tracer`, 8003) — the core. Indexes the repo,
  resolves the call graph, extracts forks, judges them, condenses to a `FlowGraph`.
- **Render agent** (`agents/render_agent/`, package `render`, 8004) — deterministic React Flow geometry.
- **Explain agent** (`agents/explain_agent/`, package `explain`, 8007) — on-demand per-node symbol
  explanations, reached via `POST /repomaps/{repo}/explain`, and on-demand endpoint API contracts,
  reached via `POST /contract` (offline `HeuristicContractWriter` fallback, no API key required).
  **Neither is part of the analyse pipeline.**
- **Frontend** (`frontend/`, Vite + React Flow) — thin renderer over backend-supplied positions.

Each service directory is the Docker build context, with `main.py` at its root and all other code in
a uniquely-named package inside it (`gateway/`, `tracer/`, …). See the skill's "Never Use Generic Top-Level Package Names" for why that nesting
is load-bearing and for the `.env` path trap it creates.

Each service is a FastAPI app run via uvicorn (VS Code task **CodeFlow: All Services**). `.env` at the
repo root holds `ANTHROPIC_API_KEY`, GitHub OAuth creds, `DATABASE_URL` and `LOCAL_REPO_PATH`. With
`ENVIRONMENT=local`, `api/gateway/core/config.py` points the agent URLs at localhost instead of
Railway. `.env` is not hot-reloaded — restart the gateway after editing. Gateway→tracer timeout is 900s.

## How a request actually flows

The live entry points are `POST /ci/analyse/local` and `POST /ci/analyse/github` (background tasks),
plus `POST /ci/analyse` for the published GitHub Action's archive upload. All are in
`api/gateway/routers/ci.py`. There is no `POST /analyse` — that router was removed as dead.

`AnalysisService.analyse` → profiler → tracer → render → persist. Progress is polled at
`GET /ci/progress?since=<seq>`.

## Run logging and progress

One call site produces both the terminal log line and the browser's progress detail, so the two can
never drift. `shared/run_log/` holds the primitives: `Console` (docker-style `[n/total]` stage lines,
grey sub-steps, green `OK`, yellow `WARN`, red `FAIL`), `EventLog` (a 500-entry ring buffer of
`LogEvent{seq, ts, level, stage, message}`), `RunFormatter`/`configure_logging(service)` (the shared
`HH:MM:SS service │ message` format, installed by every `main.py` and by the dev scripts) and
`EventLogHandler` (funnels any WARNING+ from anywhere in the process into the event log, so real
warnings reach the UI).

The gateway's `ProgressTracker` owns a `StagePlan` (`progress_plan.py`: profiler 15 / tracer 60 /
render 15 / save 10 by weight), an `EventLog` and a `Console`. `begin`/`step`/`complete`/`warn`/`fail`
each log **and** move the bar. The tracer's `StageReporter` does the same for its 15 stages
(`stage_names.py`), and `/ci/progress` merges the tracer's events into the gateway's log by `seq`, so
the browser sees one continuous stream. `snapshot(since)` returns `percent`, `percent_ceiling` (the
top of the current stage — drawn as the striped region), `phases` (the 4 top-level phases with
`done`/`active`/`pending`/`failed`), `points` (18 tick marks, each with the `at` percent it sits at,
the tracer expanded inline) and `events` after `since`. `fail()` records `failed_stage` alongside the
message; `failure_message.describe_failure` turns httpx errors into something readable
(`/trace returned 500 — ValueError: …`) rather than a bare exception class.

Frontend: `useCiProgress` polls with the last seen `seq` and accumulates events (deduped by `seq`,
reset if the server's sequence goes backwards). `RunProgress` renders the phase row, the bar with its
notches, the grey detail line, an error panel naming the failed stage, and `RunLogTerminal` — a
collapsible monospace log that opens automatically on failure.

Read endpoints (`api/gateway/routers/repo_maps.py`), all ETag'd with `304` support:
`GET /repomaps/{repo}/home` (endpoint list + description, no render call),
`GET /repomaps/{repo}/flow` (whole-repo map, serves the stored pre-rendered view),
`GET /repomaps/{repo}/flow?entry=<entry_id>` (one endpoint, sliced and rendered on demand) and
`?helper=<owner_fqn>` (one shared function). Passing both `entry` and `helper` is a 400. The
`entry`/`helper` responses carry a `links` map alongside `view`.
`GET /repomaps/{repo}/endpoint?entry=<entry_id>` returns an `EndpointDetail`: parsed method/path,
title, description, key methods with source, and an API contract (LLM-written at read time via the
explain agent, cached in `explanations`, falling back to the heuristic writer on any failure).

## The tracer pipeline

Composed by `tracer/services/analysis/flow_pipeline.py`. Each stage below is now its own package
under `tracer/services/analysis/`:

1. **Index** (`indexing/`) — function-level symbol table. Imports resolve by walking the importing
   module's ancestor prefixes longest-first (`syntax/paths.py`), so any directory layout works;
   stdlib names short-circuit the walk. Source roots are derived from where imports actually bind.
   Lanes (`ServiceRootResolver`): hints → app roots (`AppRootDeriver`: where `FastAPI()` is
   constructed, widened to the enclosing import-derived root unless two apps share it) → import-
   derived source roots → first FQN segment. No directory name is special-cased.
2. **Resolve** (`resolve/`) — call graph with per-call-site control context. `resolve/indexes.py`
   holds the thin read-indexes over it.
3. **Extract forks** (`forks/`) — branch, match, except, table, polymorphic, dynamic.
   **Routes** (`routes/`) — `fastapi_route_scanner.py` and `django_route_scanner.py` (URLconf,
   including `urlpatterns +=` under feature flags, `include()` recursion and CBVs via MRO), plus
   `entry_finder.py`.
4. **Detect effects** (`effects/`) — http/db/llm/file/queue/email/response.
5. **Judge** (`significance/`) — the LLM stage. `LlmDecisionJudge` batches ~20 forks per
   temperature-0 call, deciding `decision`/`guard`/`noise`, writing the question a human would ask
   ("User can access ticket?") and an importance score. `HeuristicDecisionJudge` wraps the old reach
   heuristic and is the offline default when no API key is present.
6. **Condense** (`condense/`) — projects onto a `FlowGraph` of entry/step/decision/parallel/effect/
   outcome nodes. `DecisionProjector` emits each decision node and, for arms that terminate without
   reaching further code, an `outcome` node labelled by `OutcomeLabeler` (`Returns`/`Raises`/
   `Continues`, or a verdict-supplied label); `decision_seeder.py` attaches decisions whose owner is
   not call-reachable from an entry.
7. **Stitch** (`stitch/`) — `HttpStitchDetector` matches outbound URLs to route entries;
   `LlmStitchDetector` judges the ones URL matching cannot resolve.
8. **Budget** (`budget/`, with scoring in `ranking/`) — folds nothing away; it demotes.
   `BudgetRecondenser`, `ArmFolder` and `EffectCapper` collapse mergeable nodes (via the shared
   `ContainerRepointer`, which re-parents onto the survivor and refuses containment cycles);
   `SequenceChainer` links same-owner body members into a `sequence` edge where safe;
   `ContainmentIndexer` computes each node's containment `level`, `hidden_children`, `body_kind` and
   `body_head`/`body_tails` from the `containers` set; `SkeletonReducer` demotes low-ranked nodes to
   a deeper level rather than deleting them. A node's `hidden_children` is exactly what its `+`
   reveals in the UI.
9. **Label** (`labelling/`) — `FlowNamer` writes `llm_label`/`llm_title`/`one_liner`; `FlowReviewer`
   checks the result. Neither may change node or edge counts.
10. **Symbol context** (`symbols/`) — builds `meta["symbol_context"]`, the per-node step tree the
    explain agent and the isolate view consume. Runs last and still walks raw AST.

Cross-cutting, at the `analysis/` root: `contracts.py` (the `Protocol` declarations),
`config.py` (`SignificanceConfig`, `BudgetConfig`), `fingerprints.py` (the four cache-key hashes),
and `syntax/` (pure AST and string helpers).

**Determinism**: same repo in → byte-identical `flow_graph.json` out. LLM verdicts are cached in
`.cache/`, content-addressed via `fingerprints.py` on the fork's source, arm labels and reach sizes
plus a `PROMPT_VERSION`. Cold run on django-helpdesk ≈4 min; warm ≈2s.

## Data models (`shared/models/flow_graph.py`)

- `FlowNode{ id, kind ∈ [entry|step|decision|parallel|effect|outcome], lane, label, llm_label,
  one_liner, backing, refs: [SourceRef], badges, folded_count, effect_kind, effect_target, level,
  hidden_children, containers, body_kind ∈ [flow|list], body_head, body_tails }`. `containers` is
  the containment parent set; everything else in that list is derived from it by `ContainmentIndexer`.
  `body_kind` is a **derivation, not an assert** — a decision's arms are mutually exclusive, so a
  fork is correctly `"list"`.
- `FlowEdge{ source, target, kind ∈ [sequence|arm|parallel|stitch], arm_label, group_id,
  confidence ∈ [resolved|inferred|dynamic], is_spine }`
- `Lane{ id, name, llm_title, entry_ids, mass }` — one per detected service root.
- `FlowGraph{ repo, page_title, lanes, nodes, edges, meta }` — sorts itself canonically on validate.
- `RenderedView{ type, nodes, edges }` — positioned React Flow nodes.

Vertical rhythm comes from one derived value: `FlowGridConfig.row_step` = tallest node geometry +
`row_gutter` (96). After placement, `VerticalStretcher` scales y when the content is much wider than
tall (`factor = clamp(aspect / 2.0, 1.0, 1.8)`), which costs nothing in zoom while `fitView` is
width-constrained and makes near-horizontal parent→child edges readable. It is a no-op at or below
aspect 2.0 — stretching a height-constrained diagram would shrink every node. The 1.8 cap is
deliberate: at 3.0 the aspect metric hits its target while the picture gets visibly worse.

The tracer's own value objects live in `tracer/models/` grouped by subject: `index_records.py`,
`call_records.py`, `sites.py`, `verdicts.py`, `naming.py`.

