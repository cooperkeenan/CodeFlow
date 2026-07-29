# PBI 39 — Diagram-edits endpoint (api gateway)

**Batch:** 12 &nbsp;|&nbsp; **Depends on:** 38 &nbsp;|&nbsp; **Read `README.md` first.**

## Why
The frontend loads a user's saved diagram edits on open and saves them (debounced) on change. This
PBI exposes GET/PUT over the store from PBI 38, scoped to the authenticated user.

## Scope

### 1. Models — `api/models/diagram_edit_model.py` (new)
- `DiagramEditsResponse{ repo: str, edits: dict }`
- `DiagramEditsPutRequest{ edits: dict }`
(`edits` is the full `{ view_id: overlay }` map — kept opaque `dict` at this layer.)

### 2. Service — `api/services/diagram_edit_service.py` (new)
One class, constructor-injected with a `DiagramEditStore` (pattern from
`api/services/code_read_service.py`):
```python
async def get(self, user_id: int, repo: str) -> dict          # -> edits map, {} when none
async def save(self, user_id: int, repo: str, edits: dict) -> None
```
`get` maps a `None` row to `{}`.

### 3. Router — `api/routers/diagram_edits.py` (new)
- `GET /diagram/edits?repo=<repo>` → `DiagramEditsResponse` (`Depends(get_current_user)`).
- `PUT /diagram/edits?repo=<repo>` body `DiagramEditsPutRequest` → `DiagramEditsResponse`
  (echoes saved edits). Auth-required. No logic in handlers beyond calling the one service method
  and using `user.id` — match `api/routers/code.py` style.

### 4. Wiring
- `api/dependencies.py`: `get_diagram_edit_store(request)` returning
  `request.app.state.diagram_edit_store` (typed `DiagramEditStore`), and `get_diagram_edit_service`
  (constructs `DiagramEditService(store)`) — mirror `get_repo_map_store` / `get_repo_map_service`.
- `api/main.py`: in `lifespan`, `app.state.diagram_edit_store = NeonDiagramEditStore(database_url)`
  and `await app.state.diagram_edit_store.ensure_schema()`; `app.include_router(diagram_edits_router)`.

## Acceptance criteria
- With a valid session, `GET /diagram/edits?repo=<repo>` returns `{repo, edits:{}}` before any save.
- `PUT` a small `{ "system": {...} }` map, then `GET` returns the same map; a second `PUT` overwrites.
- No/invalid token → `401` (same as tokens/code endpoints). CORS already covers it.

## Out of scope
- Any validation of overlay contents (frontend owns the shape); all frontend work (PBIs 40–47).
