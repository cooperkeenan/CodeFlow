# PBI 35 — Neon code store + source persistence (tracer)

**Batch:** 11 &nbsp;|&nbsp; **Depends on:** — &nbsp;|&nbsp; **Read `README.md` first.**

## Why
Click-to-view-code needs the original source at view time, but the tracer fetches every
file to a temp dir (`file_fetch_service.py`) and **discards it** — there is no database.
We persist each analyzed file to **Neon (Postgres)** at the one point where content is in
hand: `tracer_service._gather_evidence`, right after `fetch` returns `temp_dir` +
`file_paths`. Files are deduped by content hash so re-running an unchanged repo writes
nothing.

## Scope

### 1. Dependency + config
- `requirements.txt`: add `psycopg[binary]` (psycopg3, async).
- `agents/tracer_agent/core/config.py` **and** `api/core/config.py`: add
  `DATABASE_URL: str = ""`.

### 2. Store abstraction — `shared/`
- `shared/code_store/code_store.py` (new): `CodeStore` Protocol —
  `async def put_file(repo, file_path, language, content) -> None` and
  `async def get_file(repo, file_path) -> dict | None`.
- `shared/code_store/neon_code_store.py` (new): `NeonCodeStore` implementing it via an
  async psycopg connection pool built from `DATABASE_URL`. One class per file, ≤150 lines.
- `ensure_schema()` (idempotent `CREATE TABLE IF NOT EXISTS`) run on startup:
  ```sql
  code_files (
    repo         text,
    file_path    text,
    language     text,
    content      text,
    content_hash text,
    updated_at   timestamptz default now(),
    primary key (repo, file_path)
  )
  ```
  `put_file` upserts on `(repo, file_path)` and **skips the write when `content_hash`
  is unchanged**.

### 3. Persist on fetch — `agents/tracer_agent/services/source_persist_service.py` (new)
One class, constructor-injected with a `CodeStore`. Given `repo_name`, `temp_dir`,
`file_paths`: read each file, compute `sha256`, derive the repo-relative path
(`Path(p).relative_to(temp_dir)`), infer `language` from extension, and `put_file(...)`.
Key on `request.repo_name` so it matches `AnalyseResponse.repo`. Call it from
`tracer_service._gather_evidence` after a successful fetch (await it; failures log and
continue — persistence must not break tracing). Register in tracer `dependencies.py`.

## Acceptance criteria
- With `DATABASE_URL` set, after `/analyse` the `code_files` table has one row per analyzed
  file, `content` matching source, `content_hash` populated.
- Re-running on an unchanged repo performs no content rewrites (hash match).
- With `DATABASE_URL` empty/unreachable, tracing still completes (persistence is best-effort
  and logged).

## Out of scope
- Reading code back / the API endpoint (PBI 36) and all frontend work (PBI 37).
