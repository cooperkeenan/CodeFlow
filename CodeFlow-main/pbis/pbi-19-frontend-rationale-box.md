# PBI 19 — Per-view rationale box (frontend)

**Batch:** 4 &nbsp;|&nbsp; **Depends on:** PBI 17 &nbsp;|&nbsp; **Read `README.md` first.**

## Why
See *why* the layout agent chose each diagram type while clicking through views. The rationale
already reaches the frontend in `analysis.trace.diagram_templates[viewId].meta.rationale` (PBI 17).
Surface it in a small text box per view.

> **Frontend authorization:** this PBI explicitly authorizes frontend edits, overriding the usual
> "don't touch frontend" rule (consistent with README Phase-1 locked decision #5).

## Scope

### 1. Pass templates down — `frontend/src/pages/DiagramPage.jsx`
Read `trace?.diagram_templates` and pass it into `<DiagramExplorer diagramTemplates={...} />`
alongside the existing `spec` / `views` props.

### 2. Mount the box — `frontend/src/components/diagram/DiagramExplorer.jsx`
Accept the new `diagramTemplates` prop. The active view is already keyed by `graphKey`
(`focus ? `${focus.kind}:${focus.id}` : 'system'`). Mount a new `<RationaleBox>` directly below
`<Breadcrumb>` and above the graph/detail-panel flex row, passing
`diagramTemplates?.[graphKey]?.meta?.rationale` and the template `type`.

### 3. New component — `frontend/src/components/diagram/RationaleBox.jsx`
Render the rationale (and optionally the chosen `type` as a label). Match the existing
`DetailPanel.jsx` styling: `--mono` font, the `LABEL`/`VALUE` constants, dark theme variables
(`--surface`, `--border`, `--text`). If `rationale` is empty/undefined, render `null` (no empty box).

## Acceptance criteria
- Each view (system / module / component) shows its own rationale text.
- Navigating between views updates the displayed rationale to match the active `graphKey`.
- A view with no rationale renders nothing (no broken/empty box).

## Out of scope
- Generating/persisting the rationale (PBIs 17/18). This PBI only displays it.
