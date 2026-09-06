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
the code are the source of truth.

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
  explanations. **Not part of the analyse pipeline**; reached only via `POST /repomaps/{repo}/explain`.
- **Frontend** (`frontend/`, Vite + React Flow) — thin renderer over backend-supplied positions.

Each service directory is the Docker build context, with `main.py` at its root and all other code in
a uniquely-named package inside it (`gateway/`, `tracer/`, …). See `CLAUDE.md` for why that nesting
is load-bearing and for the `.env` path trap it creates.

Each service is a FastAPI app run via uvicorn (VS Code task **CodeFlow: All Services**). `.env` at the
repo root holds `ANTHROPIC_API_KEY`, GitHub OAuth creds, `DATABASE_URL` and `LOCAL_REPO_PATH`. With
`ENVIRONMENT=local`, `api/gateway/core/config.py` points the agent URLs at localhost instead of
Railway. `.env` is not hot-reloaded — restart the gateway after editing. Gateway→tracer timeout is 900s.

## How a request actually flows

The live entry points are `POST /ci/analyse/local` and `POST /ci/analyse/github` (background tasks),
plus `POST /ci/analyse` for the published GitHub Action's archive upload. All are in
`api/gateway/routers/ci.py`. There is no `POST /analyse` — that router was removed as dead.

`AnalysisService.analyse` → profiler → tracer → render → persist. Progress is polled at `GET /ci/progress`.

Read endpoints (`api/gateway/routers/repo_maps.py`), all ETag'd with `304` support:
`GET /repomaps/{repo}/home` (endpoint list + description, no render call),
`GET /repomaps/{repo}/flow` (whole-repo map, serves the stored pre-rendered view),
`GET /repomaps/{repo}/flow?entry=<entry_id>` (one endpoint, sliced and rendered on demand) and
`?helper=<owner_fqn>` (one shared function). Passing both `entry` and `helper` is a 400. The
`entry`/`helper` responses carry a `links` map alongside `view`.

## The tracer pipeline

Composed by `tracer/services/analysis/flow_pipeline.py`. Each stage below is now its own package
under `tracer/services/analysis/`:

1. **Index** (`indexing/`) — function-level symbol table. Imports resolve by walking the importing
   module's ancestor prefixes longest-first (`syntax/paths.py`), so any directory layout works;
   stdlib names short-circuit the walk. Source roots are derived from where imports actually bind.
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

## Endpoint diagrams (`shared/flow_endpoints/`)

The whole-repo map answers "what is this codebase"; it does not answer "what happens when this
endpoint is called". That second view is built **at read time in the gateway**, not in the tracer
pipeline — it slices one entry out of the stored `FlowGraph` on request.

`EndpointCatalog` lists the `entry:` nodes, splitting real HTTP routes from `entry:seed:` /
`entry:trivial:` service entry points. `EndpointSubgraph.slice(graph, entry_id)` takes the
containment closure from that entry, keeps only intra-slice edges, prunes back edges into a
deterministic DAG (`BackEdgePruner`), records which targets fell outside, and hands the result to
`EndpointElider` (`DEFAULT_BUDGET = 16`, `_MAX_PASSES = 3`), which runs:

`ChunkDissolver` (undo the whole-repo `more:`/`fold:` placeholders — there is room inside one
endpoint) → `SharedHelperCollapser` (fold owners used by ≥10 endpoints into one `helper:` node) →
`RunCollapser` (fold linear runs of ≥3 steps into one `run:` node) → then a loop of `IslandDemoter`
→ `FanoutCapper` (≤5 children per parent) → `EndpointRanker` (only if still over budget; BFS
distance, then kind, then how *exclusive* the owner is to this endpoint) → `LevelAssigner` →
`TerminalCloser` → finally `SoleChildPromoter`. Every pass has a floor of 10 nodes.

`OwnerSubgraph` slices from any `owner_fqn` rather than an entry, producing a **helper diagram** for
a shared function. It reuses `EndpointSubgraph.slice_root` — same closure, pruning and elision, just
rooted somewhere that is not an entry.

### Cross-diagram links

`LinkResolver` maps node id → `EndpointLink{kind, target, label}` for one slice. It runs at read
time and is returned **beside** `view` in the HTTP response — deliberately **not** stored on
`FlowNode`, so `flow_graph.json` is untouched and the golden check is unaffected. Four sources:

- `endlink:<entry_id>` — the cut-off call lands on another endpoint → link to that endpoint.
- `endcont:<owner_fqn>` — the cut-off call lands on ordinary code → link to that function's helper diagram.
- `helper:<owner_fqn>` — a `SharedHelperCollapser` fold → link to that helper's diagram.
- a visible terminal whose `owner_fqn` is shared by ≥2 endpoints.

Two restrictions stop the links being noise, and both were added after measurement: only **visible**
(`level == 0`) nodes are considered, since a link on a hidden node can never be clicked; and a link
is suppressed when its target owner is **already drawn in the current view**, because that just
reopens what the reader is looking at. On django-helpdesk this is 22 links across 8 of the 32 endpoint diagrams.

## Read-path caching

Endpoint views are recomputed per request — DB read, two Pydantic validations, a graph slice, and an
HTTP round trip to the render agent — so both layers cache.

Server (`api/gateway/`): `RepoMapStore.updated_at()` is a cheap `SELECT updated_at` that does **not**
read the 2–3 MB `jsonb` payload; it is the version key. `FlowGraphCache` (LRU 8) holds the validated
`FlowGraph` per `(user, repo, updated_at)`; `EndpointViewCache` (LRU 200) holds the rendered response
per `(user, repo, updated_at, view_key)` where `view_key` is `home`, `entry:<id>` or `helper:<fqn>`.
Both are app-state singletons — `deps/` builds services per request, so a per-request cache would be
useless. `shared/caching/lru_cache.py` is the shared primitive.

`ETag` is a hash of the **response body**, not of the cache key. An earlier version keyed it on
`(user, repo, updated_at, view_key)`, which meant a rendering or elision code change left
`updated_at` untouched, the server returned `304 Not Modified`, and the browser rendered a stale
diagram forever. Keep it content-derived.

Client: TanStack Query v5 (`frontend/src/api/queries.js` holds every key and fetcher in one place, so
hooks and prefetches cannot drift). `staleTime` 5min, `gcTime` 30min. Hovering an endpoint row or a
saved-map row prefetches its view, so the click is usually instant.

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

## Tech Stack
- **Python 3.10 exactly** (venv at `venv/`), FastAPI, Uvicorn, Pydantic v2. A newer interpreter
  changes `ast.unparse` output and breaks the golden diff — see `CLAUDE.md`.
- Anthropic SDK, `claude-haiku-4-5-20251001`, temperature 0 (decision judge, stitch judge, labeller).
- psycopg + Neon Postgres for persistence (`shared/repo_map_store/neon_repo_map_store.py`).
- React + Vite + React Flow, TanStack Query v5 for the read path. Positions come from the render
  agent — no dagre, no Mermaid.
- Python-only analysis; JS/TS is not traced.

## Tooling

```bash
python scripts/render_repo.py <repo> [out]        # pipeline → JSON + decision list
python scripts/render_repo.py --no-llm <repo>     # force the deterministic heuristic judge
python scripts/screenshot_flow.py <repo>          # → scratch_out/flow.png via headless Chrome
python scripts/screenshot_flow.py --save <handle> <repo>   # also save to a user account
python scripts/selfrun.py                         # in-process self-analysis (2 known failures)
python scripts/flow_agent.py <repo> <action>...   # drive the real page in a browser
python scripts/flow_metrics.py <out_dir>          # structural harness, must exit 0
python scripts/_verify_imports.py                 # all 5 services import cleanly
python scripts/render_tour.py                     # regenerate the /tour payload
python scripts/dump_explain.py <out_dir> --list   # explain-agent payload for a node
```

### `flow_agent.py` — drive the diagram without a human relaying screenshots

Playwright (dev-only, `requirements-dev.txt`; uses the installed Chrome via `channel="chrome"`, so
no browser download) opens the real `FlowPage` and runs a sequence of actions. It reports the
rendered page **as text**, so state can be asserted rather than eyeballed.

```bash
python scripts/flow_agent.py <repo> --rebuild state overlaps
python scripts/flow_agent.py <repo> "toggle:<node_id>" fit "shot:scratch_out/x.png"
python scripts/flow_agent.py <repo> "press:collapse all" state
```

Actions: `state` (every visible node with position, label, `+N` control and a `[→]` marker for a
cross-diagram link), `overlaps` (colliding node pairs — **0 is the goal**, and this is the check that
catches bad layout), `toggle:<id>`, `link:<id>` (follow a link chip), `click:<id>`,
`press:<button text>`, `key:<name>`, `fit`, `shot:<path>`, `endpoint:<entry_id>`. Flags `--entry
<entry_id>` and `--home` open one endpoint's diagram or the repo home page instead of the whole map.
`--rebuild` re-runs the pipeline first; without it the existing fixture is reused. Nested expansion works — toggle a revealed decision or a
`more:` node to go deeper.

This is also the **only** check that catches a frontend render loop — `vite build` passes happily
while the page is unusable. Run it after any `frontend/src/` change.

`screenshot_flow.py` serves the result to the real `FlowPage` through a dev-only `/flow-fixture`
route — no API, DB or login. `--save` upserts a `repo_maps` row viewable in the web UI, resolving
the account by `github_login` or `email`.

## Frontend features

- **`/` dashboard** — repo list, GitHub repo picker, run analysis (local or GitHub), progress polling.
- **`/repo` repo home** — the endpoint list (routes and service entry points) with the repo
  description; picking one opens its diagram. This is the intended way in, not the whole-repo map.
- **`/flow`** — the decision diagram. Progressive disclosure via `+` per branch, `show cross-links`,
  `collapse all`, click-to-isolate a node into a code/flowchart view, provenance popovers. Arrow keys
  pan both axes (60px, 240px with Shift), suppressed while focus is in a text field.
  `?entry=` / `?helper=` render one endpoint or one shared function.
- **Cross-diagram links** — a labelled `→ target` chip on a node opens that target's diagram. A
  breadcrumb (`← endpoints / forms.PublicTicketForm / Ticket.send / …`) shows how you got there; the
  arrow goes back one level, each ancestor is clickable. The trail lives in a `from` query param so
  it survives reload and browser back, rather than in React state.
- **Edit mode** — an `edit` toggle on the flow page turns the canvas into a draw.io-style editor:
  drag nodes, connect edges, add text, restyle arrowheads and lines, delete. Edits are stored as an
  **overlay** diffed against the rendered view and persisted per (user, repo) to Neon via
  `GET`/`PUT /diagram/edits`. `applyEdits` re-derives the view from that overlay — the overlay is the
  single source of truth, so never mirror nodes/edges into React state.
- **`/tour`** — a guided walkthrough of CodeFlow's own pipeline, generated by `scripts/render_tour.py`
  into `frontend/public/tour/codeflow_tour.json`. **It embeds `file:line` references into this repo's
  own source, so it goes stale whenever CodeFlow's files move — regenerate it after any restructure.**
- **`/settings`** — API token management for the GitHub Action.

## Known Limits (by design, worth stating rather than hiding)

- **Decisions expressed as classes are invisible.** DDD `BusinessRule.is_broken()` objects contain no
  fork, so fork detection sees nothing.
- **SDK-mediated HTTP is invisible.** Effect detection matches httpx/requests method names; a call
  made inside a third-party SDK produces no `EffectSite`.
- **Plugin/dynamic routing is invisible.** Supporting one project's service-locator idiom would mean
  hardcoding it.

## Open defects (honest, with real numbers)

- **The whole-repo map is ~18 nodes with essentially one edge between them.** The skeleton is
  component-shaped, but seed anchors are roots by definition, so most top-level nodes sit on one row
  unconnected. This is *structural* — the call graph genuinely has few edges between top-level
  components — not a layout bug. Endpoint diagrams are now the intended way in and do not have this
  problem; the whole-repo map is the weaker view.
- **Diagrams still sprawl horizontally.** Column assignment allocates width by subtree size, so a
  wide branch pushes its siblings far apart and leaves a large empty middle. Fewer nodes per view
  masked it; the underlying placement is unchanged and is the next real layout problem.
- **`PillarGatewaySelector` scores `entry:group:*` route groups 0** because its scoring reads
  `node.backing`, and route-group entries carry none (they are aggregates). They lose skeleton slots
  to less central `entry:seed:*` anchors that do have backing.
- **Chunked bodies can be `body_kind == "flow"` with `body_head == None`**, which silently disables
  chain re-routing for that body. Not yet root-caused.
- **Single-path decisions render as a command shape but are still labelled as a question.**
  `flow_node_treatment.shape_for` draws a decision with exactly one live arm as `"pipeline"`/`"rect"`
  via `is_linear`, but the label still comes from `DecisionLabeler`, which always phrases a question.
  Fixing it needs a `decision_judge_prompt.py` change and a `PROMPT_VERSION` bump.
- **Sequence bodies rarely chain** — `SequenceChainer` only links same-owner, single-arm-edge,
  same-`owner_fqn` members, so most sequence-shaped bodies render as an unordered set. Chaining one
  that fails those conditions would fabricate an edge that is not real.
- **`scripts/selfrun.py` has 2 failing assertions**, both pre-existing and deliberately left red:
  its expected lane set is stale (does not include `explain`, and `scripts` is being detected as a
  service root — possibly a lane-detection bug worth investigating), and one guard-selector decision
  survives the judge.

## Ops

`.github/workflows/cd.yml` builds the backend images and runs `railway redeploy` on push to `main`;
it is **not** gated on CI, and the frontend is not in the pipeline (served via `tunnel.sh`).
`scripts/build-push.sh` builds and pushes the same images manually.
`action.yml` + `examples/codeflow.yml` are the published GitHub Action, which posts an archive to
`POST /ci/analyse`.

## Where Things Live

- Tracer analysis: `agents/tracer_agent/tracer/services/analysis/` — `flow_pipeline.py` composes it
- Judging: `analysis/significance/` + `prompts/decision_judge_prompt.py` + `analysis/fingerprints.py`
- Entry detection: `analysis/routes/`
- Condensation/budget: `analysis/condense/`, `analysis/budget/`, `analysis/ranking/`
- Geometry: `agents/render_agent/render/placement/{flow_page_placer,tree_layout,tree_structure,flow_emit,vertical_stretcher}.py`
- Endpoint slicing, links, helper diagrams: `shared/flow_endpoints/`
- Read-path caching: `shared/caching/lru_cache.py`, `api/gateway/services/{flow_graph_cache,endpoint_view_cache,etag}.py`
- Subsystem write-ups: `decision-records/` (tracked, commit-pinned)
- Frontend flow page: `frontend/src/pages/FlowPage.jsx`, `hooks/{useGraphTransform,useFlowEditing,useArrowKeyPan}.js`,
  `components/flow/{FlowCanvas,FlowHeader,Breadcrumb,LinkChip,NodeChrome,ProvenancePopover}.jsx`
- Frontend repo home: `frontend/src/pages/RepoHomePage.jsx`, `components/repo/EndpointList.jsx`,
  `api/queries.js` (all react-query keys and fetchers)
- Persistence: `shared/repo_map_store/neon_repo_map_store.py`, `api/gateway/routers/repo_maps.py`
