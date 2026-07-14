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

The pipeline runs **profiler → tracer → layout → render → frontend**. Diagram treatment is now
**hierarchy-aware** — the higher up the codebase you are, the more the LLM interprets; the lower
down, the more deterministic.

**Top level (system view)** — shows only **runnable services** (modules with an entry marker;
`Module.is_service`, threaded profiler → tracer → layout). For CodeFlow that's `api` + the four
agents; support modules (`shared`, `frontend`, `evaluation`) are excluded. Edges use the real
module-to-module graph, with synthetic `sequence` edges filling gaps so the flow stays connected
(`services/builders/_module_edge_builder.py`). Selection lives in
`services/planning/hierarchy_classifier.py`: if any module is `is_service` it drives the set,
otherwise it falls back to the directory-prefix tree + largest-connected-component logic
(`helpers/hierarchy_tree.py`, `helpers/connected_components.py`).

**Service level (module views)** — LLM-authored **semantic steps**, not file names. For a service
module the LLM infers its purpose, picks a diagram type, and emits ≤8 behavioural steps
(e.g. `Fetch & traverse codebase → Gather evidence → …`), each carrying `backing_components` so a
step drills into the real component view. See `services/planning/service_step_planner.py`,
`helpers/service_step_validator.py`, `services/builders/_service_view_builder.py`,
`prompts/service_step_prompt.py`. Orchestrated in `services/planning/view_planner.py`. Step boxes
show the title only (no per-box description); the purpose shows in the rationale bar.

**Component level (drill-in)** — deterministic. The tracer classifies each component
`primary`/`secondary`; the render neighborhood placement lays **primaries on a horizontal spine and
stacks secondary helpers below their calling primary** (`agents/render_agent/placement/neighborhood.py`,
degrades byte-identically to the old flat layout when all-primary).

**Ops:** `ENVIRONMENT=local` routes the gateway to local agent ports; `frontend/.env.local`
`VITE_API_URL` points the browser at the local gateway; gateway→tracer/layout timeouts are 900s; a
live **progress bar** advances a checkpoint as each agent finishes
(`api/services/progress_tracker.py`, `GET /ci/progress`, polled by `RepoMapsPanel.jsx`).

## Known Caveats / Next Steps

1. **Tracer speed & density.** The tracer now includes helper components (as `tier: secondary`),
   which raised the component count (~147 for CodeFlow) and pushed run time toward the timeout — the
   count of LLM calls is unchanged (chunking is over static evidence), but output-per-call grew. If
   drill-in views feel too dense, tighten the helper-inclusion wording in
   `agents/tracer_agent/prompts/tracer_prompt.py` (readability, not speed).
2. **Orchestrator spines can still be long.** If a service genuinely calls many *primary* services,
   the spine stays wide (tiering only pulls off *helpers*). Next lever if needed: a spine-length cap
   with overflow to a side column.
3. **Large-codebase grouping deferred.** `hierarchy_classifier` can sub-cluster via the prefix tree
   when service modules exceed the node cap (8), but rendering nested `group:` views isn't wired
   (fine for CodeFlow's flat set).
4. **Cleanup.** `ClusterPlanner` / `cluster_prompt` / the zoned `_view_builder.build_module` branch
   are now dead for service modules (kept to avoid out-of-scope refactor) — a follow-up can remove them.
5. **Trace the frontend / JS** — still 0 components and no `frontend → api` edge (tracing is
   Python-only: jarviscg + Python AST).

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
