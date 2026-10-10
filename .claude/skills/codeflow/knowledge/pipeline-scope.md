# Pipeline Scope — What The Live Run Actually Sees

## 2026-09-29 — The dev scripts bypass the profiler
`render_repo.py`, `screenshot_flow.py`, `selfrun.py` and `flow_agent.py` read every `.py` file
directly. The live pipeline does not: the tracer fetches only the directories in the profiler's
blueprint (`TracerService._minimal_dirs`). Any bug that drops code in the profiler (module
detection, file-tree exclusion) is therefore invisible to every local check. This is how multi-app
repos (Trisus.Assist.Platform) silently lost whole applications: only the Orchestrator survived.

Run `scripts/profile_scope.py <repo>` whenever the profiler changes, or whenever a live run is
missing code a local run shows. It must exit 0. On django-helpdesk the fetch scope must be `['']`
(the whole repo) — the golden diff does **not** cover this, because render_repo skips the profiler.

## 2026-09-29 — Two independent causes, both needed fixing
1. Profiler `_embedded_repo_dirs` dropped any top-level dir with manifest + Dockerfile as a
   "vendored repo" — i.e. every app in a monorepo. Now only a real nested `.git` counts.
2. Tracer `ServiceRootResolver` fell back to a literal `"agents"`, so apps under any other parent
   merged into one lane and `TrivialEntryFolder` folded their endpoints together. Lanes now come
   from where `FastAPI()` is constructed (`indexing/app_root_deriver.py`).

Lesson: when "only part of the repo shows up", check **both** the fetch scope and the lane
assignment. Fixing either alone would still have looked broken.

## Demo multi-app repos (cloned to `~/github/demo/`)
| Repo | Apps | Expected routes |
|---|---|---|
| `paurakhsharma/python-microservice-fastapi` | cast-service, movie-service (both with inner `app/`) | 2, 5 |
| `GavriloviciEduard/fastapi-microservices` | pokemon-service, team-service + shared `db-models` | 5, 5 |
| `baranbartu/microservices-with-fastapi` | users, orders, gateway | 6, 2, gateway 0 (custom `@route` wrapper — known limit) |

A synthetic stress case worth recreating: two single-file FastAPI apps under a common non-`agents`
parent (`services/regulatory/main.py`, `services/mrf/main.py`) — must yield separate lanes.

## Known gaps left open
- Git submodules / nested clones are excluded on purpose (separate repos; GitHub's tree API omits
  them anyway). If a monorepo's apps are submodules, they will not be analysed.
- App-derived lanes exist only for FastAPI. Multiple Django projects in one repo still get lanes
  only from import resolution.

## 2026-09-29 — Running long jobs
A CodeFlow self-run with a cold LLM cache can hang for days. Never chain it after the golden
baseline in one foreground command — the timeout kills the whole chain and hides which part
finished. Run the golden baseline alone first; run self-runs with `run_in_background` and kill them
if they exceed ~8 min. The self-run is a smoke test only; it is never a blocker.
