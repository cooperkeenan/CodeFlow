# PBI 48 — Progress bar survives page close/reopen

**Batch:** 12 &nbsp;|&nbsp; **Depends on:** — &nbsp;|&nbsp; **Read `README.md` first.**
**Frontend changes are explicitly authorized for this PBI** (overrides the usual rule).

## Why
When Local CI is running and the user closes/reloads the page (or the laptop sleeps and the tab
reloads), the progress bar vanishes with no indication the pipeline is still running. The progress
state is actually **server-side and durable for the gateway's lifetime** — `ProgressTracker`
(`api/services/progress_tracker.py`) with `GET /ci/progress` returning `{active, percent, current,
error, ...}`. The bug is purely frontend: `RepoMapsPanel` only renders the bar while its local
`running` flag + polling interval (created inside `runCi`) are alive, and both reset on reload. Fix:
**resume from `/ci/progress` on mount** so an in-flight run reappears.

## Scope — `frontend/src/components/dashboard/RepoMapsPanel.jsx`
- Extract the poll loop from `runCi` into a reusable `startPolling()` (the `setInterval` body that
  calls `getProgress`, updates `progress`, and on `!active` clears the interval, sets `running=false`,
  clears `progress`, and refreshes maps / surfaces `error`). `runCi` calls it after a successful start.
- On mount (`useEffect`), call `getProgress()`: if `active`, set `running=true`, seed `progress`, and
  `startPolling()` — so a reload during a run immediately shows the bar again. Clear the interval on
  unmount.
- Keep the "already running" guard behavior; with resume-on-mount the button stays disabled while a
  run is active.
- Stay ≤150 lines — if it grows, extract a small `useCiProgress()` hook
  (`frontend/src/hooks/useCiProgress.js`) owning `running`/`progress`/`error` + `startPolling` +
  mount-resume, and have the panel consume it.

## Acceptance criteria
- Start Local CI, reload the page mid-run → the progress bar reappears at the current percent/stage
  and continues updating to completion, then refreshes the repo-map list.
- No active run → no bar on load (unchanged from today).
- Completion/error paths behave exactly as before (bar clears; error alert shown on failure).

## Out of scope
- Backend changes (the server already exposes durable progress); multi-user/per-run progress.
