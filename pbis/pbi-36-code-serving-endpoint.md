# PBI 36 — Code-serving endpoint (api gateway)

**Batch:** 11 &nbsp;|&nbsp; **Depends on:** 35 &nbsp;|&nbsp; **Read `README.md` first.**

## Why
The frontend needs to fetch a file's source by `(repo, file_path)` so the code panel can
display it. PBI 35 persists source to Neon; this PBI exposes a read path through the API
gateway.

## Scope

### 1. Read service — `api/services/code_read_service.py` (new)
One class, constructor-injected with a `CodeStore` (`NeonCodeStore`). One method:
```python
async def get_code(self, repo: str, file_path: str) -> dict  # {file_path, language, content}
```
Returns the stored row; raise a not-found signal (e.g. `None` / `KeyError`) when absent so
the router maps it to `404`.

### 2. Router — `api/routers/code.py` (new)
- `GET /code?repo=<repo>&path=<file_path>` wrapping exactly the one service method (no logic
  in the handler — project convention).
- Response schema (`CodeResponse`: `file_path`, `language`, `content`) lives in this file,
  next to the route.
- Missing file → `404`.

### 3. Wiring
- `api/dependencies.py`: add `get_code_store` (build `NeonCodeStore` from
  `settings.DATABASE_URL`) and `get_code_read_service`. Reuse the existing
  `app.state.http_client` pattern only if needed; the store owns its own pool.
- `api/main.py`: `app.include_router(code_router)`.

## Acceptance criteria
- `GET /code?repo=<repo>&path=api/services/analysis_service.py` returns
  `{file_path, language: "python", content: "..."}` for a previously analyzed repo.
- Unknown path → `404`, no stack trace leaked.
- CORS already covers it (same app/middleware as `/analyse`).

## Out of scope
- Frontend consumption (PBI 37).
