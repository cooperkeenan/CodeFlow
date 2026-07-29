# PBI 38 — Neon diagram-edit store (shared)

**Batch:** 12 &nbsp;|&nbsp; **Depends on:** — &nbsp;|&nbsp; **Read `README.md` first.**

## Why
Editable diagrams (draw.io-style edit mode) let a user delete/draw lines, change arrowheads, add
text boxes, and rename nodes. Those edits must **persist per user + repo**, survive refresh, and work
on the deployed (Railway) box — so they belong in **Neon (Postgres)**, not `shared/outputs/*.json`
(ephemeral, not user-scoped). Edits are stored as a single JSON blob per `(user_id, repo)` holding a
map of `view_id → overlay` (an overlay diff, applied on top of the backend-computed view).

## Scope

### 1. Store abstraction — `shared/diagram_edit_store/`
Mirror `shared/repo_map_store/` exactly.
- `shared/diagram_edit_store/diagram_edit_store.py` (new): `DiagramEditStore` **Protocol** —
  ```python
  async def get(self, user_id: int, repo: str) -> dict | None: ...
  async def upsert(self, user_id: int, repo: str, edits: dict) -> None: ...
  ```
- `shared/diagram_edit_store/neon_diagram_edit_store.py` (new): `NeonDiagramEditStore(database_url)`
  implementing it via `AsyncConnectionPool` — copy the pool/`_get_pool`/`ensure_schema` shape from
  `neon_repo_map_store.py` verbatim. One class per file, ≤150 lines.
- `shared/diagram_edit_store/__init__.py` (new).
- `ensure_schema()` (idempotent):
  ```sql
  CREATE TABLE IF NOT EXISTS diagram_edits (
      id         bigserial primary key,
      user_id    bigint not null references users(id),
      repo       text not null,
      edits      jsonb not null default '{}',
      created_at timestamptz default now(),
      updated_at timestamptz default now(),
      unique (user_id, repo)
  )
  ```
- `upsert` uses `ON CONFLICT (user_id, repo) DO UPDATE SET edits = EXCLUDED.edits, updated_at = now()`
  and wraps the dict with `psycopg.types.json.Json`.
- `get` returns `{ "repo", "edits", "updated_at" }` or `None` when absent.

## Acceptance criteria
- With `DATABASE_URL` set, `upsert(user_id, repo, {...})` then `get(user_id, repo)` round-trips the
  same `edits` dict; a second `upsert` on the same `(user_id, repo)` overwrites in place (one row).
- Two different `user_id`s for the same `repo` keep separate rows.
- Schema creation is idempotent (safe to call on every startup).

## Out of scope
- The API model/service/router/DI (PBI 39) and all frontend work (PBIs 40–47).
