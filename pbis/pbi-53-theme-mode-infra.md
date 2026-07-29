# PBI 53 — Light/dark theme infrastructure + Settings toggle + chrome light mode

**Batch:** 12 &nbsp;|&nbsp; **Depends on:** — &nbsp;|&nbsp; **Read `README.md` first.**
**Frontend changes are explicitly authorized for this PBI** (overrides the usual rule).

## Why
Users want a light mode toggled from Settings. This PBI adds the theme-mode plumbing (persisted,
app-wide) and delivers light mode for all **MUI + CSS-variable surfaces** (dashboard, settings,
login, repo-maps list, headers). The diagram canvas is handled separately in PBI 54. **Dark mode must
remain byte-identical** — light values are added as overrides, never by changing dark values.

Current theming (see `frontend/src/theme.js`, `frontend/src/index.css`, `frontend/src/main.jsx`):
one dark MUI theme + a `:root` block of CSS variables (`--bg`, `--surface*`, `--text*`, `--border*`,
`--accent`, …). Everything using `var(--…)` or MUI flips automatically once mode + `data-theme` flip.

## Scope

### 1. Theme-mode context — `frontend/src/theme/ThemeModeContext.jsx` (new)
`ThemeModeProvider` holding `mode: 'dark' | 'light'` (default `'dark'`), persisted to localStorage key
`codeflow_theme`. On mount and on change, set `document.documentElement.dataset.theme = mode`. Expose
`useThemeMode()` → `{ mode, toggle, setMode }`. No module-level mutable state — state lives in the
provider.

### 2. Theme factory — `frontend/src/theme.js`
Refactor the current default export into `makeTheme(mode)` returning the MUI theme for that mode
(keep the existing dark palette EXACTLY for `mode==='dark'`; add a light palette: e.g.
`background {default:'#F5F5F5', paper:'#FFFFFF'}`, dark text tokens, light divider `#E0E0E0`, keep
brand `secondary`/`info` `#64B5F6`; pick a light-readable primary green). Keep a default export of the
dark theme for back-compat if simplest, but `makeTheme` is the API.

### 3. Wire it — `frontend/src/main.jsx`
Wrap the app in `ThemeModeProvider`, and inside it select the MUI theme via `makeTheme(mode)` fed to
`ThemeProvider` (a tiny inner component that reads `useThemeMode()` so the MUI theme follows the
toggle). Keep `<CssBaseline/>` and `<BrowserRouter>`.

### 4. Light CSS variables — `frontend/src/index.css`
Add a `:root[data-theme="light"] { … }` block overriding every variable from the `:root` dark block
with a light value (bg/surface ladder → whites/greys, text → `rgba(0,0,0,.87/.60/.38)`, borders →
light greys, keep accents readable on light). Do NOT edit the existing dark `:root` values.

### 5. Settings toggle — `frontend/src/pages/SettingsPage.jsx`
Add an "Appearance" MUI `Paper` section with a light/dark toggle (MUI `Switch` or `ToggleButtonGroup`)
bound to `useThemeMode()`. Match the existing Settings card style.

## Acceptance criteria
- Toggling in Settings instantly re-themes dashboard, settings, login, repo-maps list, top bar, and
  anything using `var(--…)`; the choice persists across reload and routes.
- Dark mode is visually unchanged from today.
- No console errors; `npm run build` succeeds.

## Out of scope
- Diagram canvas/nodes/edges/panels (PBI 54); repo-maps caching (PBI 55).
