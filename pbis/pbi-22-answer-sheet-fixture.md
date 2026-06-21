# PBI 22 — CodeFlow structural answer-sheet fixture

**Batch:** 5 &nbsp;|&nbsp; **Depends on:** — &nbsp;|&nbsp; **Read `README.md` first.**

## Why
We need a ground truth — authored from the **source code**, not from the agent output — to compare
every run against. This fixture is the regression baseline the harness (PBI 23) scores against.

> This is a solicited **evaluation/CLI asset, not a pytest** — it does not violate the "no unsolicited
> tests" rule. Keep it as plain data + a small schema, no test framework.

## Scope

### 1. Fixture — `evaluation/answer_sheet/codeflow.json`
Encode the facts below with **tolerances** (name sets + count ranges, never exact LLM wording):
- `architecture`: multi-agent microservice pipeline — a FastAPI `api` gateway orchestrates four
  agents over HTTP; a React `frontend` calls the api.
- `modules` (7): `api`, `frontend`, `shared`, `profiler_agent`, `tracer_agent`, `layout_agent`,
  `render_agent`.
- `expected_cross_module_edges`: `frontend→api`, `api→profiler_agent`, `api→tracer_agent`,
  `api→layout_agent`, `api→render_agent` (all HTTP). NOTE in the file: the
  `profiler→tracer→layout→render` sequence is a *data* dependency orchestrated by `api`, **not** a
  direct call — documented, not asserted as an edge.
- `orchestrators` / `entry_points`: `AnalysisService` (api, primary orchestrator); each agent's entry
  service (`ProfilerService`, `TracerService`, `LayoutService`, render's entry service);
  `GitHubService`.
- `shared`: pure data models, no outgoing edges (consumed by all modules).
- `component_count_ranges` (per module, sane bands; tune from the current run): api ~12–18,
  layout_agent ~12–18, tracer_agent ~10–16, profiler_agent ~8–14, render_agent ~5–10, shared ~10–18,
  **frontend > 0** (deliberately flags the known JS-not-traced gap as a miss).

### 2. Schema — next to the harness (e.g. `evaluation/answer_sheet/schema.py`)
A small dataclass / pydantic model describing the fixture shape, so PBI 23 loads it typed. Type
annotations on all fields; prefer a dataclass for the value object.

## Acceptance criteria
- `codeflow.json` validates against its schema and reflects the real source, independent of any run.
- The fixture is human-readable and easy to extend (adding a module or edge is a one-line change).

## Out of scope
- The comparison logic and scorecard (PBI 23).
- Grading diagram types or descriptions (we grade structural facts only this round).
