# CodeFlow — Project Context

## What This Is
CodeFlow is a multi-agent system that generates architecture diagrams from GitHub repositories or
local codebases. It profiles the repo structure, traces the call graph, and renders a React Flow
diagram in the browser.

## Workflow

Feature work follows a three-step loop:

1. **Opus plans** — breaks the work into small, self-contained scoped task docs ("PBIs") and designs
   the approach.
2. **Sonnet implements** — Opus spawns a Sonnet sub-agent to implement each scoped task in the repo.
3. **Opus reviews** — Opus reviews the resulting diff before it is accepted.

Scoped task docs are ephemeral (gitignored, deleted on merge to main), so don't depend on their
numbers or existence — treat this file and the code as the source of truth.

## Architecture

Five independent services, plus a frontend:

- **Gateway** (`api/`, port 8000) — orchestrates the pipeline and serves the UI's HTTP API.
  Endpoints: `/analyse`, `/analyse/local`, `/analyse/local/from-profile`,
  `/analyse/local/from-trace`, `/github/...`.
- **Profiler agent** (`agents/profiler_agent/`, port 8002) — discovers the repo's module/zone
  skeleton and produces a `RepoBlueprint`.
- **Tracer agent** (`agents/tracer_agent/`, port 8003) — fetches the source for each blueprint
  directory, builds an evidence bundle (AST signatures + jarviscg call graph + confirmed edges),
  and produces a hierarchical `DiagramSpec` (components carry `role`/`tier`; cross-service HTTP edges
  recovered).
- **Layout agent** (`agents/layout_agent/`, port 8006) — classifies the module hierarchy, chooses a
  **diagram type per view**, and builds a `DiagramTemplate` (nodes / edges / meta) for every
  navigable view. The **top-level view shows only runnable services** (modules with an entry point —
  see `is_service` below); **service (module) views are LLM-authored semantic steps** (≤8 behavioural
  steps, each backed by real components for drill-down); component views are typed per-component.
  Type/step choice is LLM-driven (temperature 0); ordering/edge/placement math is deterministic.
- **Render agent** (`agents/render_agent/`, port 8004) — converts each `DiagramTemplate` into a
  `RenderedView` with **deterministic React Flow positions** per type (no Mermaid, no dagre).
- **Frontend** (`frontend/`, Vite + React Flow) — a thin renderer over the backend-supplied
  positions; it applies theme/styling only.

Each service is a FastAPI app launched via uvicorn (VS Code task **CodeFlow: All Services**). The
venv at `venv/` ships `jarviscg` for the tracer's call-graph step. `.env` at the repo root holds
`ANTHROPIC_API_KEY`, GitHub OAuth creds, `LOCAL_REPO_PATH`, and `ENVIRONMENT`. When
`ENVIRONMENT=local`, `api/core/config.py` forces the four agent URLs to their localhost ports
(8002/8003/8004/8006 — the tasks.json services) instead of the deployed Railway hosts. The frontend
proxies to the gateway via `frontend/.env.local`'s `VITE_API_URL` (set to `http://localhost:8000`
for local; the deployed URL to test against production). `.env` is not hot-reloaded — restart the
gateway after editing it. The gateway→tracer/layout HTTP timeouts are 900s (LLM-heavy calls).

## Pipeline (request flow)

`POST /analyse {repo_name, local_path|access_token}`

1. Gateway calls profiler `/profile` → `RepoBlueprint`.
2. Gateway builds `TracerRequest{blueprint, ...}` and calls tracer `/trace` →
   `TracerResponse{diagram_spec}`.
3. Gateway calls layout `/layout` → `{layout_hint, diagram_spec (enriched), diagram_templates}`
   (one `DiagramTemplate` per view: `system`, `module:*`, `component:*`).
4. Gateway calls render `/render {diagram_templates}` → `{views}` (one `RenderedView` per view id).
5. Gateway returns `{repo, profile, trace (diagram_spec + diagram_templates), diagram (views)}`;
   cached to `shared/outputs/*.json` (full response in `tracer_output.json`).

## Design Principle: Facts vs Interpretation

The whole pipeline is built around separating what we can derive **deterministically** from the
codebase from what an **LLM** is asked to interpret, and validating the LLM's output against the
facts.

**Deterministic (identical every run):**
- Module boundaries (entry/package markers — see below)
- Directory groups per module
- AST signatures, import graph, jarviscg call graph, `confirmed_edges`
- Component placement into module/zone (by longest matching directory prefix on `file_path`)
- IO and edges (from evidence)

**LLM (constrained, temperature 0, validated):**
- Free-text architecture/language/framework labels
- Zone role labels and descriptions (`presentation`/`business`/`data`/`tools`/`config`/…)
- Which components are architecturally meaningful + their descriptions
- The **diagram type per view** (the layout agent picks; node ordering, edge synthesis, and React
  Flow placement remain deterministic per type)

**Validators** (`BlueprintValidator`, `GraphValidator`) drop anything the LLM produces that isn't
backed by the deterministic skeleton.

No vector DB, no embeddings, no hand-maintained architecture templates. There used to be five
`shared/templates/*.json` files forcing every repo into a flat 3-band layout; those are gone.

## Module Detection Rule (important)

`agents/profiler_agent/core/module_markers.py` defines two marker sets, used by
`ModuleDetector` (`agents/profiler_agent/services/module_detector.py`):

- **PACKAGE markers** — `pyproject.toml`, `setup.py`, `package.json`, `go.mod`, `Cargo.toml`,
  `pom.xml`, `build.gradle`, `Dockerfile`. Any directory containing one is a module root.
- **ENTRY markers** — `main.py`, `app.py`, `manage.py`. A directory with an entry marker only
  becomes a module **if it is not enclosed by a package root**.

Deliberately NOT markers: `docker-compose.yml` (monorepo orchestrator, not a single boundary) and
`requirements.txt` (too common at monorepo root). This is why:

- CodeFlow (root `docker-compose.yml` only, no Dockerfile/pyproject at root) → 6 modules: `api`,
  `frontend`, `shared`, `profiler_agent`, `render_agent`, `tracer_agent`.
- A repo with a root `Dockerfile` and `src/api/app.py` → 1 module rooted at `""`, with `src/api/`,
  `src/domain/`, etc. as zones.

## Data Models

Shared at `shared/models/`:

- `RepoBlueprint{ architecture_type, language, framework, patterns, modules: [ModulePlan] }`
- `ModulePlan{ name, description, root_path, style, is_service, zones: [ZonePlan] }`
- `ZonePlan{ name, description, directories: [str] }`
- `DiagramSpec{ architecture_type, modules: [Module], edges, external_actors, entry_points,
  layout_hint }`
- `Module{ name, description, root_path, purpose, is_service, zones: dict[str, list[Component]],
  cluster_plan }` — `is_service` (set by the profiler when the module has an entry marker) drives the
  top-level architecture view: only service modules appear there.
- `Component{ name, description, file_path, io, children, role, tier, nested }` — the tracer now
  assigns `tier` (`primary`|`secondary`): primaries form the component-view spine, secondaries branch
  off to the side.
- `Edge{ source, target, edge_type ∈ [http|import|database|event|call|sequence] }`
- `LayoutHint{ archetype, module_order, rank_assignments, rationale }`

Layout/render (`shared/models/diagram_template.py`):

- `DiagramTemplate{ type ∈ [pipeline|hub_and_spoke|layered_tier|hierarchy|mesh|dependency_graph|
  relationship|zoned], nodes: [TemplateNode], edges: [TemplateEdge], meta }` — type-specific data
  (hub id, depth/tier maps, ordered steps, folded members, per-view `rationale`) rides in `meta`.
- `TemplateNode{ id, label, tier, module_name, kind ∈ [module|component|zone|cluster], parent,
  style, drillable, backing_components }` — `backing_components` maps an LLM-authored semantic step
  back to the real component(s) it represents, so a step still drills into the component view.
- `RenderedView{ type, nodes, edges }` — positioned React Flow nodes + styled edges.

There used to be a flat `DiagramSpec.layers: dict[zone_name, list[Component]]` and a separate
`LayerHints` model — both are gone.

## Tech Stack
- Python 3.10+, FastAPI + Uvicorn, Pydantic v2, `pydantic-settings`.
- Anthropic SDK (`anthropic`), model `claude-haiku-4-5-20251001`, temperature 0 (profiler, tracer,
  and layout agents; render is deterministic, no LLM).
- `jarviscg` for the call graph (Python only — JS/TS is not traced yet).
- React + Vite + React Flow for the frontend; positions come from the render agent (no dagre in the
  system path).

## Current Status

The pipeline runs **profiler → tracer → layout → render → frontend** and produces **one
decision-flow page** for the whole codebase — no drill-down. The design and per-stage spec live in
`features/` and `docs/decision_flow_tracer.md`. The governing principle: **static analysis owns
100% of structure; the LLM only names things.** The tracer output is byte-identical across runs.

**Tracer (`agents/tracer_agent/services/analysis/`)** — a pure static pipeline, no LLM. It indexes
the repo to a function-level symbol table (`project_indexer.py`), resolves a call graph with
per-call-site control context (`call_resolver.py`), extracts **dispatch sites** — the seven forms of
divergence: branch/match/except/table/route/polymorphic/dynamic (`dispatch_extractor.py`) — and I/O
**effects** (http/db/llm/response, `effect_detector.py`). A deterministic **significance filter**
(`significance_filter.py`) separates real decisions from guards via reach-set mutual exclusivity,
then **condensation** (`flow_condenser.py`) projects everything onto a `FlowGraph` of
entry/step/decision/parallel/effect nodes. **Stitching** (`flow_stitcher.py`) matches outbound HTTP
effects to route entries in other services, and the **budget** (`page_budgeter.py`) folds the graph
to one bounded page. Composed by `flow_pipeline.py`; `TracerResponse.flow_graph` is the payload.

**Layout (`agents/layout_agent`)** — the ONLY LLM stage. `FlowLabeler` makes one temperature-0 call
that can only fill in human labels keyed to ids the pipeline issued (`flow_labeler.py`,
`helpers/flow_label_validator.py`); on failure it returns the graph with deterministic labels.

**Render (`agents/render_agent/placement`)** — LLM-free geometry. `FlowPagePlacer` lays the graph out
as horizontal swimlanes (one per service), left→right with a bold happy-path spine, effects
right-aligned, and cross-lane stitch edges in the gutter — byte-identical coordinates.

**Frontend (`frontend/src/pages/FlowPage.jsx`)** — a single React Flow canvas that renders the
`RenderedView` verbatim, with per-kind node shapes, a legend, and a `file:line` provenance popover.

Self-run acceptance: `python scripts/selfrun.py` runs the whole pipeline in-process on CodeFlow.

**Ops:** `ENVIRONMENT=local` routes the gateway to local agent ports; `frontend/.env.local`
`VITE_API_URL` points the browser at the local gateway; gateway→tracer/layout timeouts are 900s; a
live **progress bar** advances a checkpoint as each agent finishes
(`api/services/progress_tracker.py`, `GET /ci/progress`, polled by `RepoMapsPanel.jsx`).

## Known Caveats / Next Steps

1. **Budget tuning (the top open decision).** `lane.mass = Σ decision scores + Σ route-arm counts`
   lets a large API surface dominate: CodeFlow's `api` lane (20 routes) takes ~75% of the budget and
   folds every lane's decisions/effects into `+N` chips, so the page is entry-heavy. The graph is
   healthy pre-budget (3 decisions, 47 effects, 49 steps). Options: dampen the route-count term in
   `lane_builder.py`, group routes by router into fewer entries, fold excess entries *before*
   effects/decisions in `page_budgeter.py`, or raise `BudgetConfig.node_budget`. Best judged against
   the rendered page — the constants are one-line changes.
2. **CodeFlow is a near-linear pipeline.** Only ~3 genuine decisions exist across the whole repo, and
   most are guard/fallback shaped, so the honest page is mostly entries → steps → effects with cross-
   service stitches. Branchy repos will surface more decisions; this is the design working, not a bug.
3. **api gateway orchestration** is rewired for the core `analyse` path + the new `GET
   /repomaps/{repo}/flow` endpoint; the persisted-artifact shape (`RepoMapDetail.map.diagram`) now
   holds the `RenderedView` — confirm the store round-trips it end-to-end in a live run.
4. **Trace the frontend / JS** — still Python-only (the tracer front end is `ast`-based). A JS/TS
   front end would let the `frontend → api` calls stitch too.

## Where Things Live (quick map)

- Pipeline orchestration + progress: `api/services/analysis_service.py`, `api/services/progress_tracker.py` (`GET /ci/progress`)
- Profiler skeleton + `is_service`: `agents/profiler_agent/services/{module_detector,repo_map_service,blueprint_validator,profiler_service}.py`
- Tracer evidence + assembly + tiering: `agents/tracer_agent/services/{evidence_service,ast_service,call_graph_service,spec_assembler,graph_validator,tracer_service}.py`, `agents/tracer_agent/prompts/tracer_prompt.py`
- Layout hierarchy + views (planners): `agents/layout_agent/services/planning/{hierarchy_classifier,view_planner,service_step_planner,template_planner,cluster_planner,component_type_planner,template_selector_service}.py`
- Layout helpers: `agents/layout_agent/helpers/{hierarchy_tree,connected_components,service_step_validator,module_graph}.py`; models in `agents/layout_agent/models/{hierarchy,service_step}.py`; config in `core/hierarchy_config.py`
- Layout builders: `agents/layout_agent/services/builders/{_service_view_builder,_component_view_builder,_view_builder,_template_builder,_module_edge_builder}.py`
- Render placement: `agents/render_agent/services/placement_service.py`, `agents/render_agent/placement/*` (spine/branch in `neighborhood.py`)
- Frontend graph transform + components: `frontend/src/hooks/useGraphTransform.js`, `frontend/src/hooks/graph/common.js`, `frontend/src/components/diagram/{FlowGraph,CustomNode,ModuleGroupNode,ZoneGroupNode,DiagramExplorer,Breadcrumb,DetailPanel,RationaleBox}.jsx`
- Shared outputs (cached): `shared/outputs/profiler_output.json`, `shared/outputs/tracer_output.json`
- Prompts: `agents/profiler_agent/prompts/profiler_prompt.py`, `agents/tracer_agent/prompts/tracer_prompt.py`, `agents/layout_agent/prompts/{semantic_prompt,cluster_prompt,component_type_prompt,template_prompt}.py`
