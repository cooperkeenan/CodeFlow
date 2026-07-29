# PBI 54 — Light mode for the diagram canvas, nodes, edges & panels

**Batch:** 12 &nbsp;|&nbsp; **Depends on:** 53 &nbsp;|&nbsp; **Read `README.md` first.**
**Frontend changes are explicitly authorized for this PBI** (overrides the usual rule).

## Why
PBI 53 themes the app chrome but the diagram view is hardcoded dark hex across ~8 files. Make the
diagram follow the theme, using the CSS variables + `data-theme` from PBI 53. **Dark mode must remain
byte-identical** — achieve light mode by (a) swapping hardcoded hex for the existing CSS variables
whose dark value already equals that hex, and/or (b) adding `[data-theme="light"]` CSS overrides. Do
not change any dark appearance.

Hex → variable map (dark values are unchanged): `#121212`→`var(--bg)`, `#1A1A1A`→`var(--surface)`,
`#1E1E1E`→`var(--surface-2)`, `#242424`→`var(--surface-3)`/`var(--border)`, `#2C2C2C`→`var(--surface-4)`,
`#333333`→`var(--surface-5)`/`var(--border-hi)`, text `rgba(255,255,255,.87/.60/.50/.38)`→
`var(--text)`/`var(--text-medium)`/`var(--text-disabled)`.

## Scope

### 1. Canvas chrome — `frontend/src/components/diagram/FlowGraph.jsx`
Replace hardcoded hex in the `<Background>` (both edit + view variants), `<Controls>`, `<MiniMap>`,
and any container styles with the CSS variables above. The grid `color`/`background` must read from
variables so it lightens under `data-theme="light"` (add a `--grid` variable in index.css: dark
`#242424`/edit faint, light a subtle grey). Keep the edit-mode faint grid behavior.

### 2. Panels & bars (hex → variables)
`frontend/src/components/diagram/{DiagramExplorer,DetailPanel,CodePanel,RationaleBox,Breadcrumb}.jsx`
and `frontend/src/components/diagram/edit/EditToolbar.jsx`: swap hardcoded surface/border/text hex for
the variables. In `CodePanel.jsx`, switch the react-syntax-highlighter style to a light Prism theme
(`vs`) when `data-theme==='light'` (read `document.documentElement.dataset.theme`), else keep
`vscDarkPlus`.

### 3. Nodes — `frontend/src/components/diagram/CustomNode.jsx` (+ ModuleSummaryNode, TextNode, group nodes)
Dark mode keeps the per-module palette (colored dark cards) exactly as today. For light mode, add a
className to each node's root (e.g. `cf-node`, `cf-node-title`, `cf-node-desc`) and add
`[data-theme="light"] .cf-node { … }` overrides in a stylesheet (extend
`frontend/src/components/diagram/edit/editCanvas.css` or a new `diagramTheme.css` imported by
FlowGraph) so light mode uses a light card surface with dark text, while keeping the module **accent**
(border + zone label) from the inline palette so modules stay colour-coded. Use `!important` only
where React Flow inline styles must be beaten (precedent: existing handle CSS).

### 4. Edges — `frontend/src/hooks/graph/common.js` + `edit/edgeMarkers.js`
Make the neutral edge stroke (and its `markerEnd.color`) read from a theme variable (add
`--edge` / `--edge-dim` in index.css: dark = current `#333333`/`#242424`, light = mid-greys that read
on white). Keep the flow/sequence purple and the selected-edge CSS override. Ensure `markerEnd.color`
matches the stroke in both modes (if a CSS var can't be used inside the marker object, resolve via
`getComputedStyle` once or pick a fixed mid-grey that works on both — implementer's call, but arrows
must stay visible in light mode).

## Acceptance criteria
- With light mode on, the diagram canvas, grid, minimap, controls, breadcrumb, rationale box, detail
  panel, code panel, edit toolbar, nodes, and edges are all light-readable (dark text on light
  surfaces; arrows/edges visible).
- Toggling back to dark reproduces today's exact appearance.
- Drill-down, edit mode, and code view all work in both themes; `npm run build` succeeds.

## Out of scope
- Perfect per-module colour tuning for light mode (a first pass to iterate on is acceptable).
