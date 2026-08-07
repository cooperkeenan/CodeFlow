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

## Vocabulary

- **Frame** — the large rectangle a node becomes when you click its `isolate` control. The node
  itself grows to ~78% of the canvas, its outline turns dashed halfway through, the rest of the
  diagram dims and drifts aside. The frame shows the node's title at top-centre and, below it, the
  symbol that node resolves to: the source file, the class or function, and its methods and helpers
  each with a plain-English one-line summary. Use "frame" for this; it is not a panel, popover or
  modal — it is the node. Its right column toggles between a **code view** (the selected method's
  source) and a **sequence view** (the whole class's calls, in source-line order).
- Frame content is fetched **on demand** from `POST /repomaps/{repo}/explain` and cached by
  content-addressed fingerprint in the `ExplanationStore`, so explanations are never generated for
  every node up front. `flow_graph.meta.symbol_context` (written by `SymbolContextBuilder`) is what
  makes that possible: it carries each node's owning FQN plus the function/class table, so the
  explain agent can be handed just the source slices it needs.

## Architecture

Six services plus a frontend:

- **Gateway** (`api/`, 8000) — orchestrates the pipeline, serves the UI's HTTP API, persists results.
- **Profiler agent** (`agents/profiler_agent/`, 8002) — repo module/zone skeleton → `RepoBlueprint`.
- **Tracer agent** (`agents/tracer_agent/`, 8003) — the core. Indexes the repo, resolves the call
  graph, extracts forks, judges them, condenses to a `FlowGraph`.
- **Layout agent** (`agents/layout_agent/`, 8006) — cosmetic labelling of the finished graph.
- **Render agent** (`agents/render_agent/`, 8004) — deterministic React Flow geometry.
- **Explain agent** (`agents/explain_agent/`, 8007) — on-demand plain-English summaries of the symbol
  behind a node; what fills the **frame**. Called by the gateway's `NodeExplainService`, never by the
  pipeline, so it costs nothing until a user opens a frame.
- **Frontend** (`frontend/`, Vite + React Flow) — thin renderer over backend-supplied positions.

Each is a FastAPI app run via uvicorn (VS Code task **CodeFlow: All Services**). `.env` at the repo
root holds `ANTHROPIC_API_KEY`, GitHub OAuth creds, `DATABASE_URL` and `LOCAL_REPO_PATH`. With
`ENVIRONMENT=local`, `api/core/config.py` points the five agent URLs at localhost instead of Railway.
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
   entry/step/decision/parallel/effect/outcome nodes. `DecisionProjector` emits each decision node
   and, for arms that terminate without reaching further code, an `outcome` node labelled by
   `OutcomeLabeler` (`Returns`/`Raises`/`Continues`, or a verdict-supplied label);
   `decision_seeder.py` attaches decisions whose owner is not call-reachable from an entry.
7. **Stitch** (`flow_stitcher.py`) — `HttpStitchDetector` matches outbound URLs to route entries;
   `LlmStitchDetector` judges the ones URL matching cannot resolve.
8. **Budget** (`visibility_budgeter.py`) — folds nothing away; it demotes. `BudgetRecondenser`,
   `ArmFolder` and `EffectCapper` collapse mergeable nodes (via the shared `ContainerRepointer`,
   which re-parents onto the survivor and refuses containment cycles); `SequenceChainer` links
   same-owner body members into a `sequence` edge where safe; `ContainmentIndexer` computes each
   node's containment `level`, `hidden_children`, `body_kind` and `body_head`/`body_tails` from the
   `containers` set; `SkeletonReducer` demotes low-ranked nodes to a deeper level rather than
   deleting them. A node's `hidden_children` is exactly what its `+` reveals in the UI.

**Determinism**: same repo in → byte-identical `flow_graph.json` out. LLM verdicts are cached in
`.cache/decision_verdicts.json`, content-addressed on the fork's source, arm labels and reach sizes
plus a `PROMPT_VERSION`. Cold run on django-helpdesk ≈4 min; warm ≈3s.

## Data models (`shared/models/flow_graph.py`)

- `FlowNode{ id, kind ∈ [entry|step|decision|parallel|effect|outcome], lane, label, llm_label,
  one_liner, backing, refs: [SourceRef], badges, folded_count, effect_kind, effect_target, level,
  hidden_children, containers, body_kind ∈ [flow|list], body_head, body_tails }`. `containers` is
  the containment parent set; everything else in that list is derived from it by
  `ContainmentIndexer` — see `HANDOFF.md` §2 for what each field means and why `body_kind` is a
  derivation, not an assert.
- `FlowEdge{ source, target, kind ∈ [sequence|arm|parallel|stitch], arm_label, group_id,
  confidence ∈ [resolved|inferred|dynamic], is_spine }`
- `Lane{ id, name, llm_title, entry_ids, mass }` — one per detected service root.
- `FlowGraph{ repo, page_title, lanes, nodes, edges, meta }` — sorts itself canonically on validate.
- `RenderedView{ type, nodes, edges }` — positioned React Flow nodes.

## Tech Stack
- Python 3.10+, FastAPI, Uvicorn, Pydantic v2.
- Anthropic SDK, `claude-haiku-4-5-20251001`, temperature 0 (decision judge, stitch judge, labeller,
  symbol explainer). Every LLM call is cached and content-addressed on a `PROMPT_VERSION`.
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
python scripts/flow_agent.py <repo> <action>...   # drive the real page in a browser
```

### `flow_agent.py` — drive the diagram without a human relaying screenshots

Playwright (dev-only, `requirements-dev.txt`; uses the installed Chrome via `channel="chrome"`, so
no browser download) opens the real `FlowPage` and runs a sequence of actions. It reports the
rendered page **as text**, so state can be asserted rather than eyeballed.

```bash
python scripts/flow_agent.py <repo> --rebuild state overlaps
python scripts/flow_agent.py <repo> "toggle:<node_id>" fit "shot:scratch_out/x.png"
python scripts/flow_agent.py <repo> "press:collapse all" state
python scripts/flow_agent.py <repo> "toggle:<parent>" "isolate:<child>" isolated dimmed
```

Actions: `state` (every visible node with position, label and `+N` control), `overlaps` (colliding
node pairs — **0 is the goal**, and this is the check that catches bad layout), `toggle:<id>`,
`isolate:<id>` (opens the frame), `isolated` (the frame's box, canvas fill and computed border),
`dimmed`, `click:<id>`, `key:<name>`, `press:<button text>`, `fit`, `shot:<path>`. `--rebuild`
re-runs the pipeline first; without it the existing fixture is reused. Nested expansion works —
toggle a revealed decision or a `more:` node to go deeper.

`screenshot_flow.py` serves the result to the real `FlowPage` through a dev-only `/flow-fixture`
route — no API, DB or login. `--save` upserts a `repo_maps` row viewable in the web UI, resolving
the account by `github_login` or `email`.

**Frame content needs a repo**, so `/flow-fixture` accepts `?repo=<name>` (`App.jsx: fixtureAnalysis`)
purely so the harness can exercise it; stub the response with Playwright's
`page.route("**/explain", ...)`. Without a repo the hook short-circuits and the frame correctly reads
`no explanation available for this node`. Animation assertions must allow for the frame's ~920ms
open plus a 760ms camera pan — `FlowSession.isolate` waits 1300ms for exactly this reason, and
reading sooner produces a half-grown box that looks like a regression but is not.

## Current Status

The pipeline produces one progressive-disclosure decision page per repo: a ≤15-node skeleton always
visible, with a `+` per branch revealing nested decisions and outcomes via `hidden_children`. On the
demo target `django-helpdesk` the judge finds **222** decisions, all revealable, with labels like
*"User can access ticket?"* and *"Create new ticket or update only?"*.

For the current honest list of open defects with real numbers — the top level's thin connectivity,
a gateway-selector scoring gap, a chain-linking gap, a mislabelled single-arm decision shape — see
`HANDOFF.md` §6. That file is the gap analysis; this file stays a primer.

## Known Limits (by design, worth stating rather than hiding)

- **Decisions expressed as classes are invisible.** DDD `BusinessRule.is_broken()` objects contain no
  fork, so fork detection sees nothing.
- **SDK-mediated HTTP is invisible.** Effect detection matches httpx/requests method names; a call
  made inside a third-party SDK produces no `EffectSite`.
- **Plugin/dynamic routing is invisible.** Supporting one project's service-locator idiom would mean
  hardcoding it.

## Ops

`.github/workflows/cd.yml` builds six backend images (including `explain`) and runs `railway redeploy` on push to `main`;
it is **not** gated on CI, and the frontend is not in the pipeline (served via `tunnel.sh`).
`scripts/build-push.sh` builds and pushes the same images manually.

## Where Things Live

- Tracer analysis: `agents/tracer_agent/services/analysis/` — `flow_pipeline.py` composes it
- Judging: `llm_decision_judge.py`, `heuristic_decision_judge.py`, `decision_judge_factory.py`,
  `prompts/decision_judge_prompt.py`, `verdict_cache.py`, `decision_fingerprint.py`
- Entry detection: `fastapi_route_scanner.py`, `django_route_scanner.py`, `entry_finder.py`
- Condensation/budget: `flow_condenser.py`, `decision_seeder.py`, `visibility_budgeter.py`,
  `containment_indexer.py`, `container_repointer.py`, `budget_config.py`
- Geometry: `agents/render_agent/placement/{flow_page_placer,tree_layout,tree_structure,flow_emit}.py`
- Frontend flow page: `frontend/src/pages/FlowPage.jsx`, `hooks/useGraphTransform.js`,
  `hooks/useExpansion.js`, `components/flow/{FlowCanvas,NodeChrome,CameraController}.jsx`
- The frame (isolate): `frontend/src/hooks/{useIsolatedView,useIsolateAnimation,ExplanationCacheContext,
  useNodeExplanation}.js`, `components/flow/isolateLayout.js`, `components/flow/isolate/*` —
  see `HANDOFF.md` §5 for the animation invariants
- Explain path: `api/services/{node_explain_service,symbol_context_resolver}.py`,
  `agents/explain_agent/`, `agents/tracer_agent/services/analysis/symbol_context_builder.py`,
  `shared/explain_prompt_version.py`
- Persistence: `shared/repo_map_store/neon_repo_map_store.py`, `api/routers/repo_maps.py`
