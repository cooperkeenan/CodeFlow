# PBI 49 — Dashboard: "Select GitHub Repo" button + picker

**Batch:** 12 &nbsp;|&nbsp; **Depends on:** — &nbsp;|&nbsp; **Read `README.md` first.**
**Frontend changes are explicitly authorized for this PBI** (overrides the usual rule).

## Why
The dashboard can only "Run Local CI" against the configured `LOCAL_REPO_PATH`. Add a second action
next to it that lets the user pick one of their **GitHub repositories** and run the full analysis
pipeline on it. All backend endpoints already exist — this is frontend-only.

Existing pieces to reuse (do NOT add backend code):
- `frontend/src/api/github.js` → `listRepos(accessToken)` (GET `/github/repos`), `startGithubOAuth()`.
- `frontend/src/api/analysis.js` → `runAnalysis('/analyse', { access_token, repo_name })` (returns the
  same `{repo, profile, trace, diagram}` map shape that `onOpenMap` already consumes; the gateway
  also saves it to the user's repo maps).
- The GitHub token is returned as `github_access_token` on GitHub sign-in
  (`SignInResponse`, read in `App.jsx` as `d.github_access_token`) — today it is NOT persisted.

## Scope

### 1. Persist the GitHub token — `frontend/src/api/session.js`
Add `saveGithubToken(t)` / `getGithubToken()` / clear it inside `clearSession()`, using a
`codeflow_github_token` localStorage key (mirror the existing session-token helpers).

### 2. Capture it on sign-in — `frontend/src/App.jsx`
In the `exchangeCode(code)` success branch, call `saveGithubToken(d.github_access_token)` alongside
`saveSession(...)`. (Leave the `linkGithub` branch as-is; it returns no token.)

### 3. Picker dialog — `frontend/src/components/dashboard/GithubRepoPicker.jsx` (new)
A MUI `Dialog` (open/onClose props). On open, `listRepos(getGithubToken())`, filter to
`language === 'Python'` (same filter as `hooks/useGitHub.js`), and render a searchable `List` of
`full_name` (+ description). Selecting a repo calls `onSelect(fullName)`. Show loading + error states
(mirror `RepoMapsPanel` patterns). ≤150 lines; keep list-row markup terse.

### 4. Wire the button — `frontend/src/components/dashboard/RepoMapsPanel.jsx`
- Add a **"Select GitHub Repo"** button (MUI `GitHubIcon`) next to "Run Local CI".
- Click: if `getGithubToken()` is present → open `GithubRepoPicker`; else → `startGithubOAuth()`.
- On picker `onSelect(fullName)`: set a local `analysing` flag (disable both buttons, show text
  "Analysing <repo>…"), call `runAnalysis('/analyse', { access_token: getGithubToken(), repo_name:
  fullName })`; on success `onOpenMap(result)` (navigates to the diagram); on failure surface via the
  existing error alert; always clear `analysing`. Keep the file ≤150 lines — if it grows, lift the
  GitHub-run logic into a tiny `hooks/useGithubAnalysis.js`.

## Acceptance criteria
- With a GitHub-signed-in user, "Select GitHub Repo" opens a dialog listing their Python repos;
  picking one runs `/analyse` and navigates to the generated diagram; the new map also appears in the
  Repo Maps list on return.
- With no stored GitHub token, the button starts GitHub OAuth instead of opening an empty dialog.
- Errors show in the existing alert; buttons disable while analysing; "Run Local CI" behavior and the
  progress-bar resume (PBI 48) are unchanged.

## Out of scope
- Backend changes; a progress bar for `/analyse` (it doesn't drive `ProgressTracker` — a spinner/text
  is fine); non-Python repo support.
