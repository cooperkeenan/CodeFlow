# PBI 37 — Frontend: code-view toggle + code panel

**Batch:** 11 &nbsp;|&nbsp; **Depends on:** 34, 36 &nbsp;|&nbsp; **Read `README.md` first.**
**Frontend changes are explicitly authorized for this PBI** (overrides the usual rule).

## Why
Deliver the user-facing feature: a masthead **"code view" toggle**. While on, clicking any
component that maps to a code file shows that file's source in a side panel, auto-scrolled
to and highlighting the component's definition; clicking another component updates the panel
automatically. Toggle off restores normal drill/detail behavior. The component→location
data already rides on `trace.diagram_spec` (PBI 34); source is fetched from `/code`
(PBI 36).

## Scope

### 1. Plumbing
- `frontend/package.json`: add `react-syntax-highlighter`.
- `frontend/vite.config.js`: add `/code` to the dev proxy (alongside `/analyse`, `/github`).
- `frontend/src/api/code.js` (new): `fetchCode(repo, path)` → `GET /code?repo=&path=` via the
  existing `request` wrapper in `api/client.js`.

### 2. Masthead toggle — `frontend/src/pages/DiagramPage.jsx`
Add a toggle button to the existing `.diagram-header` (top-right). Lift `codeViewMode`
state here; pass `codeViewMode` and `repo` into `DiagramExplorer`. Style as a small
mono/`--accent` pill consistent with `Badge`.

### 3. Click handling — `frontend/src/components/diagram/DiagramExplorer.jsx`
- Build a `componentLocations` map from `spec` (walk `modules[].zones{}.components[]` →
  `name → {file_path, start_line, end_line}`), memoized.
- Add `codePanel` state.
- In `handleNodeClick`: **if `codeViewMode` and `componentLocations[label]` exists**, set
  `codePanel` to that location + label and return (do not drill, do not open DetailPanel).
  Otherwise keep all existing behavior. Module-summary nodes (no `file_path`) still drill.
- Render `<CodePanel>` in the right-hand slot (mirror DetailPanel placement, ~line 64-68);
  clear it on view navigation, like `detailPanel`.

### 4. Code panel — `frontend/src/components/diagram/CodePanel.jsx` (new)
- Props: `repo`, `label`, `file_path`, `start_line`, `end_line`, `onClose`.
- Fetch via `fetchCode(repo, file_path)`; render with `react-syntax-highlighter`:
  `showLineNumbers`, `wrapLines`, and `lineProps(ln)` highlighting `start_line..end_line`.
- On load, `scrollIntoView` the start line (ref/id on the first highlighted line).
- Style per existing tokens (`#121212` bg, IBM Plex Mono, `--accent #39FF14`); header with
  `label` + `file_path` + close `×`, mirroring `DetailPanel`.
- Graceful states: loading, and "source unavailable" on `404`/empty.

## Acceptance criteria
- Toggle off → diagram behaves exactly as today (drill + DetailPanel).
- Toggle on → clicking a component shows its file scrolled to / highlighting its class;
  clicking another component swaps the content automatically without re-toggling.
- A file backing multiple components scrolls to each component's own class when clicked.
- 404/unknown source shows the unavailable state, not a crash.

## Out of scope
- Per-function (sub-class) ranges; editing; multi-file tabs.
