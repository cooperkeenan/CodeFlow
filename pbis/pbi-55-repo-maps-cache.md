# PBI 55 — Cache the repo-maps list across navigation

**Batch:** 12 &nbsp;|&nbsp; **Depends on:** — &nbsp;|&nbsp; **Read `README.md` first.**
**Frontend changes are explicitly authorized for this PBI** (overrides the usual rule).

## Why
Opening a repo map navigates `/` → `/diagram`; coming back remounts `DashboardPage` → `RepoMapsPanel`,
whose `maps` state resets to `[]` and re-fetches, so the list **disappears and flickers** every time.
Cache the list above the route boundary so it shows instantly on return and refreshes in the
background. No module-level mutable state (per CLAUDE.md) — hold it in a React provider mounted above
`<Routes>`, which does not unmount on navigation.

## Scope

### 1. Provider — `frontend/src/hooks/RepoMapsContext.jsx` (new)
`RepoMapsProvider` holding `maps`, `error`, and a `refresh()` that calls `listRepoMaps()` (from
`api/repomaps`) and updates state (mirror the current fetch in `RepoMapsPanel`). Fetch once on mount.
Expose `useRepoMaps()` → `{ maps, error, refresh }`.

### 2. Mount above routes — `frontend/src/App.jsx`
Wrap `<Routes>` (or the authed area) in `<RepoMapsProvider>` so its state survives route changes.

### 3. Consume — `frontend/src/components/dashboard/RepoMapsPanel.jsx`
Replace the local `maps`/`mapError`/`refresh` fetch logic with `useRepoMaps()`. Keep everything else
(the CI + GitHub run buttons, progress bar, open-map click). `useCiProgress(refresh)` and the GitHub
run should call the context `refresh` so a completed run updates the shared list.

## Acceptance criteria
- Open a repo map, then go back → the list is shown immediately with no empty flash; a background
  refresh still picks up newly generated maps.
- Running Local CI or a GitHub analysis still refreshes the list on completion.
- `npm run build` succeeds; no `RepoMapsPanel` regressions.

## Out of scope
- Caching the full analysis payload per repo (only the list); server-side changes.
