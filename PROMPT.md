# CodeFlow — Project Context

## What This Is
CodeFlow generates a **decision diagram** from a Python codebase. It finds every point where the
code branches, has an LLM judge which of those are decisions a human would actually put on a mental
model of the system, and renders them as a tree with `file:line` provenance on every node.

The governing idea: **static analysis owns structure; the LLM judges significance and writes
labels.** The LLM may never add, remove, merge or rewire a node or edge.

## Workflow

1. **Opus plans** — breaks work into small, self-contained scoped task docs ("PBIs").
2. **Sonnet implements** — Opus spawns a Sonnet sub-agent per scoped task.
3. **Opus reviews** — reviews the diff against that task's acceptance before accepting it.

Scoped task docs are ephemeral (gitignored, deleted on merge to main). This file, `CLAUDE.md` and
the code are the source of truth. `HANDOFF.md` holds the current job and gap analysis.

## Architecture

Five services plus a frontend:

- **Gateway** (`api/`, 8000) — orchestrates the pipeline, serves the UI's HTTP API, persists results.
- **Profiler agent** (`agents/profiler_agent/`, 8002) — repo module/zone skeleton → `RepoBlueprint`.
- **Tracer agent** (`agents/tracer_agent/`, 8003) — the core. Indexes the repo, resolves the call
  graph, extracts forks, judges them, condenses to a `FlowGraph`.
- **Layout agent** (`agents/layout_agent/`, 8006) — cosmetic labelling of the finished graph.
- **Render agent** (`agents/render_agent/`, 8004) — deterministic React Flow geometry.
- **Frontend** (`frontend/`, Vite + React Flow) — thin renderer over backend-supplied positions.

Each is a FastAPI app run via uvicorn (VS Code task **CodeFlow: All Services**). `.env` at the repo
root holds `ANTHROPIC_API_KEY`, GitHub OAuth creds, `DATABASE_URL` and `LOCAL_REPO_PATH`. With
`ENVIRONMENT=local`, `api/core/config.py` points the four agent URLs at localhost instead of Railway.
`.env` is not hot-reloaded — restart the gateway after editing. Gateway→tracer/layout timeouts are
900s.

## The tracer pipeline

Composed by `services/analysis/flow_pipeline.py`:

1. **Index** (`project_indexer.py`) — function-level symbol table. Imports resolve by walking the
   importing module's ancestor prefixes longest-first (`path_fqn.py`), so any directory layout works;
   stdlib names short-circuit the walk. Source roots are derived from where imports actually bind.
2. **Resolve** (`call_resolver.py`) — call graph with per-call-site control context.
3. **Extract forks** (`dispatch_extractor.py`) — branch, match, except, route, table, polymorphic,
   dynamic. Route entries come from `fastapi_route_scanner.py` and `django_route_scanner.py`
   (URLconf, including `urlpatterns +=` under feature flags, `include()` recursion and CBVs via MRO).
4. **Detect effects** (`effect_detector.py`) — http/db/llm/file/queue/email/response.
5. **Judge** (`significance_filter.py` → `DecisionJudge`) — the LLM stage. `LlmDecisionJudge` batches
   ~20 forks per temperature-0 call, deciding `decision`/`guard`/`noise`, writing the question a
   human would ask ("User can access ticket?") and an importance score. `HeuristicDecisionJudge`
   wraps the old reach heuristic and is the offline default when no API key is present.
6. **Condense** (`flow_condenser.py`) — projects onto a `FlowGraph` of
   entry/step/decision/parallel/effect nodes; `decision_seeder.py` attaches decisions whose owner is
   not call-reachable from an entry.
7. **Stitch** (`flow_stitcher.py`) — `HttpStitchDetector` matches outbound URLs to route entries;
   `LlmStitchDetector` judges the ones URL matching cannot resolve.
8. **Budget** (`page_budgeter.py`) — folds to a bounded page (`node_budget=40`,
   `visible_decisions=8`).

**Determinism**: same repo in → byte-identical `flow_graph.json` out. LLM verdicts are cached in
`.cache/decision_verdicts.json`, content-addressed on the fork's source, arm labels and reach sizes
plus a `PROMPT_VERSION`. Cold run on django-helpdesk ≈4 min; warm ≈3s.

## Data models (`shared/models/flow_graph.py`)

- `FlowNode{ id, kind ∈ [entry|step|decision|parallel|effect], lane, label, llm_label, one_liner,
  backing, refs: [SourceRef], badges, folded_count, effect_kind, effect_target }`
- `FlowEdge{ source, target, kind ∈ [sequence|arm|parallel|stitch], arm_label, group_id,
  confidence ∈ [resolved|inferred|dynamic], is_spine }`
- `Lane{ id, name, llm_title, entry_ids, mass }` — one per detected service root.
- `FlowGraph{ repo, page_title, lanes, nodes, edges, meta }` — sorts itself canonically on validate.
- `RenderedView{ type, nodes, edges }` — positioned React Flow nodes.

## Tech Stack
- Python 3.10+, FastAPI, Uvicorn, Pydantic v2.
- Anthropic SDK, `claude-haiku-4-5-20251001`, temperature 0 (decision judge, stitch judge, labeller).
- psycopg + Neon Postgres for persistence (`shared/repo_map_store/neon_repo_map_store.py`).
- React + Vite + React Flow. Positions come from the render agent — no dagre, no Mermaid.
- Python-only analysis; JS/TS is not traced.

## Tooling

```bash
python scripts/render_repo.py <repo> [out]        # pipeline → JSON + decision list
python scripts/render_repo.py --no-llm <repo>     # force the deterministic heuristic judge
python scripts/screenshot_flow.py <repo>          # → scratch_out/flow.png via headless Chrome
python scripts/screenshot_flow.py --save <handle> <repo>   # also save to a user account
python scripts/selfrun.py                         # in-process self-analysis, 5 assertions
```

`screenshot_flow.py` serves the result to the real `FlowPage` through a dev-only `/flow-fixture`
route — no API, DB or login. `--save` upserts a `repo_maps` row viewable in the web UI, resolving
the account by `github_login` or `email`.

## Current Status

The pipeline produces one decision page per repo. On the demo target `django-helpdesk` the judge
finds **225** decisions with labels like *"User can access ticket?"* and *"Create new ticket or
update only?"*.

**The two open problems**, both detailed in `HANDOFF.md`:

1. **Only a fraction of decisions reach the graph** — 225 judged, 43 nodes, 8 rendered. Ranking
   cannot promote what was never condensed in.
2. **The layout is not yet a tree.** `placement/tree_layout.py` implements a correct tidy tree, but
   it is handed a forest with many roots and faithfully draws disconnected islands.

The next feature is **progressive disclosure**: one always-visible high-level diagram, with `+`/`−`
per branch splicing the in-between decisions in place. `FlowNode.folded_count` and the `chip` in
`NodeChrome.jsx` are the hooks; nothing consumes a click yet.

## Known Limits (by design, worth stating rather than hiding)

- **Decisions expressed as classes are invisible.** DDD `BusinessRule.is_broken()` objects contain no
  fork, so fork detection sees nothing.
- **SDK-mediated HTTP is invisible.** Effect detection matches httpx/requests method names; a call
  made inside a third-party SDK produces no `EffectSite`.
- **Plugin/dynamic routing is invisible.** Supporting one project's service-locator idiom would mean
  hardcoding it.

## Ops

`.github/workflows/cd.yml` builds five backend images and runs `railway redeploy` on push to `main`;
it is **not** gated on CI, and the frontend is not in the pipeline (served via `tunnel.sh`).
`scripts/build-push.sh` builds and pushes the same images manually.

## Where Things Live

- Tracer analysis: `agents/tracer_agent/services/analysis/` — `flow_pipeline.py` composes it
- Judging: `llm_decision_judge.py`, `heuristic_decision_judge.py`, `decision_judge_factory.py`,
  `prompts/decision_judge_prompt.py`, `verdict_cache.py`, `decision_fingerprint.py`
- Entry detection: `fastapi_route_scanner.py`, `django_route_scanner.py`, `entry_finder.py`
- Condensation/budget: `flow_condenser.py`, `decision_seeder.py`, `page_budgeter.py`,
  `decision_admitter.py`, `budget_config.py`
- Geometry: `agents/render_agent/placement/{flow_page_placer,tree_layout,tree_structure,flow_emit}.py`
- Frontend flow page: `frontend/src/pages/FlowPage.jsx`, `hooks/useGraphTransform.js`,
  `components/flow/{FlowCanvas,NodeChrome,ProvenancePopover}.jsx`
- Persistence: `shared/repo_map_store/neon_repo_map_store.py`, `api/routers/repo_maps.py`
