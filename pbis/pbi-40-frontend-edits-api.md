# PBI 40 — Frontend: diagram-edits API helper + proxy

**Batch:** 12 &nbsp;|&nbsp; **Depends on:** 39 &nbsp;|&nbsp; **Read `README.md` first.**
**Frontend changes are explicitly authorized for this PBI** (overrides the usual rule).

## Why
The edit-mode UI (later PBIs) needs to load and save edits via the gateway. Add the thin API module
and dev-proxy entry, matching existing conventions, so the rest of the frontend work has a stable
data path.

## Scope

### 1. API module — `frontend/src/api/diagrams.js` (new)
Use the existing `request` wrapper (`src/api/client.js`), mirroring `src/api/repomaps.js`:
```js
import { request } from './client'
export const getDiagramEdits  = (repo) =>
  request(`/diagram/edits?repo=${encodeURIComponent(repo)}`)
export const saveDiagramEdits = (repo, edits) =>
  request(`/diagram/edits?repo=${encodeURIComponent(repo)}`, {
    method: 'PUT', body: JSON.stringify({ edits }),
  })
```

### 2. Dev proxy — `frontend/vite.config.js`
Add `/diagram` to the proxied-paths allowlist (alongside `/analyse`, `/github`, `/code`, `/ci`, …).

## Acceptance criteria
- From the running frontend, `getDiagramEdits(repo)` returns `{repo, edits:{}}` for a fresh repo and
  `saveDiagramEdits(repo, {...})` succeeds (auth header attached automatically by `request`).
- Dev server proxies `/diagram/*` to the gateway (no CORS error in the browser console).

## Out of scope
- Merge logic (PBI 41), state hook (PBI 42), and UI (PBIs 43–47).
