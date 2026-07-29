# PBI 51 — Background GitHub analysis with progress

**Batch:** 12 &nbsp;|&nbsp; **Depends on:** 50 &nbsp;|&nbsp; **Read `README.md` first.**

## Why
GitHub analysis currently runs via a synchronous `POST /analyse` the frontend awaits in one long
request — no progress bar, and it dies if the page reloads. Local CI already solves this: it runs as
a background task and `AnalysisService.analyse()` **already** advances the shared `ProgressTracker`
through profiler→tracer→layout→render. Mirror the local-CI pattern for GitHub so the **same
`/ci/progress` bar** works (and survives reload) for GitHub runs.

## Scope

### 1. Service — `api/services/github_ci_service.py` (new)
Mirror `api/services/local_ci_service.py`. Constructor-injected with `AnalysisService`,
`RepoMapService`, a way to read the user's stored GitHub token (the `UserStore` or the service from
PBI 50), and `ProgressTracker`.
```python
async def run(self, user_id: int, repo_name: str) -> AnalyseResponse
async def run_background(self, user_id: int, repo_name: str) -> None
```
`run`: fetch the stored token (raise `HTTPException(400)` if missing), call
`self._analysis.analyse(AnalyseRequest(repo_name=repo_name, access_token=token))`, then
`await self._repo_maps.save(user_id, result, source="ci-github")`. `run_background`: try/except around
`run`, on failure `self._progress.fail(str(exc))` and log (same shape as `LocalCiService`).

### 2. Endpoint — `api/routers/ci.py`
Add `POST /ci/analyse/github` (auth-required) with body `{ repo_name: str }`. Mirror
`/ci/analyse/local`: if `progress.snapshot()["active"]` return `{"started": False, "busy": True}`;
else `progress.start()`, `http_request.app.state.analysis_task =
asyncio.create_task(service.run_background(user.id, repo_name))`, return `{"started": True}`.

### 3. Wiring — `api/dependencies.py`
`get_github_ci_service(...)` mirroring `get_local_ci_service`, injecting the deps above.

## Acceptance criteria
- `POST /ci/analyse/github {repo_name}` with a linked user returns `{started:true}` immediately, and
  `GET /ci/progress` then advances profiler→tracer→layout→render exactly like local CI.
- On completion the repo map is saved (source `ci-github`) and appears in `/repomaps`.
- A second concurrent request while active returns `{started:false, busy:true}`.
- Missing/unlinked GitHub token → clean `400` (run fails via `progress.fail`, no crash).

## Out of scope
- Frontend (PBI 52). Per-run/multi-user progress (single shared tracker, same as local CI today).
