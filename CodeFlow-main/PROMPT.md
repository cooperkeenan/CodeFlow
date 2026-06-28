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
- **Layout agent** (`agents/layout_agent/`, port 8005) — chooses a **diagram type per view**
  (system / module / component), enriches the spec, and builds a `DiagramTemplate`
  (nodes / edges / meta) for every navigable view. Type choice is LLM-driven (temperature 0) over
  rich descriptions; ordering/edge/placement math is deterministic.
- **Render agent** (`agents/render_agent/`, port 8004) — converts each `DiagramTemplate` into a
  `RenderedView` with **deterministic React Flow positions** per type (no Mermaid, no dagre).
- **Frontend** (`frontend/`, Vite + React Flow) — a thin renderer over the backend-supplied
  positions; it applies theme/styling only.

Each service is a FastAPI app launched via uvicorn. The venv at `venv/` ships `jarviscg` for the
tracer's call-graph step. `.env` at the repo root holds `ANTHROPIC_API_KEY`, GitHub OAuth creds,
and `LOCAL_REPO_PATH`.

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
- `ModulePlan{ name, description, root_path, style, zones: [ZonePlan] }`
- `ZonePlan{ name, description, directories: [str] }`
- `DiagramSpec{ architecture_type, modules: [Module], edges, external_actors, entry_points,
  layout_hint }`
- `Module{ name, description, root_path, purpose, zones: dict[str, list[Component]], cluster_plan }`
- `Component{ name, description, file_path, io, children, role, tier, nested }`
- `Edge{ source, target, edge_type ∈ [http|import|database|event|call|sequence] }`
- `LayoutHint{ archetype, module_order, rank_assignments, rationale }`

Layout/render (`shared/models/diagram_template.py`):

- `DiagramTemplate{ type ∈ [pipeline|hub_and_spoke|layered_tier|hierarchy|mesh|dependency_graph|
  relationship|zoned], nodes: [TemplateNode], edges: [TemplateEdge], meta }` — type-specific data
  (hub id, depth/tier maps, ordered steps, folded members, per-view `rationale`) rides in `meta`.
- `TemplateNode{ id, label, tier, module_name, kind ∈ [module|component|zone|cluster], parent,
  style, drillable }`
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

The pipeline now runs **profiler → tracer → layout → render → frontend** (a **layout agent** was
added between tracer and render). The layout agent chooses a **diagram type per view** (system /
module / component) and builds a `DiagramTemplate` (nodes / edges / meta); the render agent computes
deterministic React Flow positions per type; the frontend is a thin renderer. (The earlier Mermaid
output is retired.)

**Working today:**
- The **system view** renders as **hub-and-spoke** (the api gateway orchestrates the four agents).
- **Component views** are typed by an LLM from rich tracer descriptions: an orchestrator that runs
  its helpers **in sequence** renders as a **pipeline** with an ordered `caller → orchestrator →
  step…` chain (synthesized "sequence" edges, drawn distinctly from literal calls) and a rationale
  shown in the UI.
- Cross-service **HTTP edges** are recovered (`api → each agent`).
- The component-type selector is **hardened** — it chunks its LLM calls, keeps partial results, and
  logs fallbacks loudly, so one failure no longer silently reverts every view to hub-and-spoke.

**In progress — service-centric abstraction (has a known bug):**
- *Goal:* high-level views should surface the meaningful **services** and fold thin single-callee
  adapter/tool components into them; drilling into a service shows its tool + service + helpers in a
  bordered container, with the caller feeding in.
- *Bug:* the graph contraction runs only over a focus's **direct callees**, but the services sit
  **one hop deeper** (they are the tools' callees), so they're never in the set and nothing folds —
  high-level views still show the tool wrappers. *Fix:* pull each direct single-callee adapter's
  callee (the service) into the view set, contract, then rebuild the callee list from the survivors.
  Logic in `agents/layout_agent/services/_view_builder.py` (`build_component`) and
  `services/_graph_contraction.py`.

## Next Steps

1. Fix the service contraction (pull services one hop deeper into orchestrator/service views) and
   verify the container drill-down renders.
2. Verify module-level contraction actually folds (`_build_structural_module`).
3. Trace the **frontend / JS** — currently 0 components and a missing `frontend → api` edge, because
   tracing is Python-only (jarviscg + Python AST).

## Where Things Live (quick map)

- Pipeline orchestration: `api/services/analysis_service.py`
- Profiler skeleton: `agents/profiler_agent/services/{module_detector,repo_map_service,blueprint_validator,profiler_service}.py`
- Tracer evidence + assembly: `agents/tracer_agent/services/{evidence_service,ast_service,call_graph_service,spec_assembler,graph_validator,tracer_service}.py`
- Layout type selection + templates: `agents/layout_agent/services/{layout_service,semantic_layout_service,cluster_planner,component_type_planner,view_planner,_view_builder,_edge_builder,_graph_contraction}.py`
- Render placement: `agents/render_agent/services/placement_service.py`, `agents/render_agent/placement/*`
- Frontend graph transform + components: `frontend/src/hooks/useGraphTransform.js`, `frontend/src/hooks/graph/common.js`, `frontend/src/components/diagram/{FlowGraph,CustomNode,ModuleGroupNode,ZoneGroupNode,DiagramExplorer,Breadcrumb,DetailPanel,RationaleBox}.jsx`
- Shared outputs (cached): `shared/outputs/profiler_output.json`, `shared/outputs/tracer_output.json`
- Prompts: `agents/profiler_agent/prompts/profiler_prompt.py`, `agents/tracer_agent/prompts/tracer_prompt.py`, `agents/layout_agent/prompts/{semantic_prompt,cluster_prompt,component_type_prompt,template_prompt}.py`
