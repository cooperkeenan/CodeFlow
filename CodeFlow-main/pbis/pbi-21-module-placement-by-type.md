# PBI 21 — Module placement honors the diagram type (render)

**Batch:** 5 &nbsp;|&nbsp; **Depends on:** PBI 20 &nbsp;|&nbsp; **Read `README.md` first.**

## Why
`render_agent/services/placement_service.py` hardcodes `place_key = "module"` for every module view,
so module placement ignores `template.type` and always draws the zone grid — the reason every module
"looks the same." System and component views already dispatch by type; make module views do the same.

## Scope

### 1. Dispatch — `agents/render_agent/services/placement_service.py`
Replace the hardcoded module branch (the `place_key = "module"` line) with type dispatch:
- `template.type == "zoned"` → the zone-grid placement.
- structural types → reuse the existing **`component_<type>`** placement functions (a module view is
  a flat component graph, exactly like a component view), i.e. `place_key = f"component_{template.type}"`.

### 2. Registry — `agents/render_agent/placement/registry.py`
Register the existing zone-grid placement (`_place_module_view`) under the `zoned` key (rename the
current `"module"` entry, or add `"zoned"`). Keep `_place_module_view`'s implementation as-is.

### 3. Verify inputs
Confirm the `component_<type>` functions consume the flat nodes + `meta` (`hub_id`, `depth_map`)
that PBI 20 now produces for structural module templates. Adjust only if a field they read is missing.

## Acceptance criteria
- A `hub_and_spoke` module renders as a hub radial, `pipeline` as a left→right chain, `hierarchy` as
  a tree, `layered_tier` as tiers; a `zoned` module renders exactly as today.
- The diagram-type label shown in the UI now matches the rendered shape.
- Two `/analyse` runs on the same repo produce identical positions and types (temperature 0).
- System and component views are unchanged.

## Out of scope
- The layout-side type + template shape (PBI 20). The answer-sheet work (PBIs 22/23).
