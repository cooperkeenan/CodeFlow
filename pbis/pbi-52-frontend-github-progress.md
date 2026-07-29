# PBI 52 — Frontend: GitHub picker via stored token + unified progress

**Batch:** 12 &nbsp;|&nbsp; **Depends on:** 50, 51 &nbsp;|&nbsp; **Read `README.md` first.**
**Frontend changes are explicitly authorized for this PBI** (overrides the usual rule).

## Why
Make "Select GitHub Repo" work for **linked** users (no client token) and give GitHub runs the same
live progress bar as local CI. Backend now exposes `GET /github/my-repos` (PBI 50) and
`POST /ci/analyse/github` (PBI 51) — a background job that drives `/ci/progress`.

## Scope

### 1. API helpers
- `frontend/src/api/github.js`: add `listMyRepos()` → `request('/github/my-repos')` (auth via the
  wrapper; no token arg).
- `frontend/src/api/ci.js`: add `runGithubCi(repoName)` → `POST /ci/analyse/github` with
  `{ repo_name: repoName }`.

### 2. Picker uses the stored token — `frontend/src/components/dashboard/GithubRepoPicker.jsx`
Replace `listRepos(getGithubToken())` with `listMyRepos()`. Drop the `getGithubToken` import.

### 3. Unify the run through progress polling — `frontend/src/hooks/useCiProgress.js`
Add `startGithubRun(repoName)` alongside `startRun`: same guard/`setRunning`/error handling, but calls
`runGithubCi(repoName)` then `startPolling()`. Both share the existing polling + on-mount resume, so
the bar (and reload-resume from PBI 48) work for GitHub identically. Keep ≤150 lines.

### 4. Panel wiring — `frontend/src/components/dashboard/RepoMapsPanel.jsx`
- The "Select GitHub Repo" button always opens the picker (token is server-side now) — no OAuth
  branch, no `analysing`/`useGithubAnalysis` synchronous path.
- On picker `onSelect(fullName)`: close picker and call `startGithubRun(fullName)` from `useCiProgress`.
- The existing `running` bar now covers GitHub too; on completion `onComplete`/`refresh()` lists the
  new map (user clicks it to open — same UX as local CI). Keep both buttons disabled while `running`.

### 5. Remove now-dead client-token code
- Delete `frontend/src/hooks/useGithubAnalysis.js` (superseded by `startGithubRun`).
- `frontend/src/api/session.js`: remove `saveGithubToken`/`getGithubToken` and the
  `codeflow_github_token` key (no longer used); keep `clearSession` valid.
- `frontend/src/App.jsx`: remove the `saveGithubToken(d.github_access_token)` call and its import
  (revert to prior behavior). No unused imports anywhere.

## Acceptance criteria
- As a **linked** user, "Select GitHub Repo" opens a dialog of your repos (no re-auth); picking one
  starts a background run, the progress bar advances profiler→tracer→layout→render, and the new map
  appears in the list on completion; clicking it opens the diagram.
- Reloading mid-GitHub-run resumes the bar (PBI 48).
- Local CI unchanged; no references to the removed helpers remain; `npm run build` succeeds.

## Out of scope
- Auto-navigating to the diagram on completion (parity with local CI = refresh the list).
