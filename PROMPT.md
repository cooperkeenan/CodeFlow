# CodeFlow — Project Context

## What This Is
CodeFlow is a multi-agent system that generates architecture diagrams from GitHub repositories or
local codebases. It profiles the repo structure, traces the call graph, and renders a React Flow
diagram in the browser.

## Architecture

Four independent services, plus a frontend:

- **Gateway** (`api/`, port 8000) — orchestrates the pipeline and serves the UI's HTTP API.
  Endpoints: `/analyse`, `/analyse/local`, `/analyse/local/from-profile`,
  `/analyse/local/from-trace`, `/github/...`.
- **Profiler agent** (`agents/profiler_agent/`, port 8002) — discovers the repo's module/zone
  skeleton and produces a `RepoBlueprint`.
- **Tracer agent** (`agents/tracer_agent/`, port 8003) — fetches the source for each blueprint
  directory, builds an evidence bundle (AST signatures + jarviscg call graph + confirmed edges),
  and produces a hierarchical `DiagramSpec`.
- **Render agent** (`agents/render_agent/`, port 8004) — converts the `DiagramSpec` to nested
  Mermaid.
- **Frontend** (`frontend/`, Vite + React Flow) — renders the `DiagramSpec` directly as a
  module → zone → component graph (Mermaid is a secondary output).

Each service is a FastAPI app launched via uvicorn. The venv at `venv/` ships `jarviscg` for the
tracer's call-graph step. `.env` at the repo root holds `ANTHROPIC_API_KEY`, GitHub OAuth creds,
and `LOCAL_REPO_PATH`.

## Pipeline (request flow)

`POST /analyse {repo_name, local_path|access_token}`

1. Gateway calls profiler `/profile` → `RepoBlueprint`.
2. Gateway builds `TracerRequest{blueprint, ...}` and calls tracer `/trace` →
   `TracerResponse{diagram_spec}`.
3. Gateway calls render `/render` → Mermaid string.
4. Gateway returns `{repo, profile, trace, mermaid}`; cached to `shared/outputs/*.json`.

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
- `DiagramSpec{ architecture_type, modules: [Module], edges, external_actors, entry_points }`
- `Module{ name, description, root_path, zones: dict[str, list[Component]] }`
- `Component{ name, description, file_path, io, children }`
- `Edge{ source, target, edge_type ∈ [http|import|database|event|call] }`

There used to be a flat `DiagramSpec.layers: dict[zone_name, list[Component]]` and a separate
`LayerHints` model — both are gone.

## Tech Stack
- Python 3.10+, FastAPI + Uvicorn, Pydantic v2, `pydantic-settings`.
- Anthropic SDK (`anthropic`), model `claude-haiku-4-5-20251001`, temperature 0.
- `jarviscg` for the call graph (Python only).
- React + Vite + React Flow + dagre for the frontend.

## Current Status

**Profiler beef-up — DONE and verified end-to-end.** Replaced the rigid 5-template profiler with
the deterministic-repo-map + constrained-LLM-labeling design above. Verified:

- CodeFlow analysis → 6 per-agent modules each with their own internal zones,
  ~53 components, 0 misplaced. Module set + placement are identical across runs;
  zone labels and edge curation vary slightly (the LLM layer, by design).
- Aetos.ScraperV2-main (single-app repo with root `Dockerfile`) → 1 module with
  `presentation/business/data/domain/tools/config` zones and accurate external actors.
- Backend import-clean; `vite build` passes.

**GitHub OAuth bug — FIXED.** OAuth redirect was landing on the homepage because `App.jsx`
always remounted into `useState('home')`. Now seeds `view` to `'github'` when the URL has a
`?code=` param so the `useGitHub` hook can exchange the code.

## Where Things Live (quick map)

- Pipeline orchestration: `api/services/analysis_service.py`
- Profiler skeleton: `agents/profiler_agent/services/{module_detector,repo_map_service,blueprint_validator,profiler_service}.py`
- Tracer evidence + assembly: `agents/tracer_agent/services/{evidence_service,ast_service,call_graph_service,spec_assembler,graph_validator,tracer_service}.py`
- Mermaid renderer: `agents/render_agent/services/{mermaid_service,module_renderer,edge_renderer}.py`
- Frontend graph transform + components: `frontend/src/hooks/useGraphTransform.js`, `frontend/src/components/diagram/{FlowGraph,CustomNode,ModuleGroupNode,ZoneGroupNode,DiagramExplorer,Breadcrumb,DetailPanel}.jsx`
- Shared outputs (cached): `shared/outputs/profiler_output.json`, `shared/outputs/tracer_output.json`
- Prompts: `agents/profiler_agent/prompts/profiler_prompt.py`, `agents/tracer_agent/prompts/tracer_prompt.py`
