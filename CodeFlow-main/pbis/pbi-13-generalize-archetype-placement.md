# PBI 13 — Generalize archetype placement to component nodes (render side)

**Phase:** 3. **Depends on:** PBI 7 (schema). **Pairs with:** PBI 12. **Read `README.md` first.**

## Why
The six archetype placers (`agents/render_agent/placement/pipeline.py`, `hub_and_spoke.py`, …) assume **module** semantics: they emit `id="mod__{module_name}"` and `type="moduleSummary"`. Component views need `id=<component name>` and `type="custom"` (as `relationship.py` does). Option B (PBI 12) makes component views select these archetypes, so the same shape geometry must be usable for component nodes.

## Scope

### 1. Separate geometry from node construction — `agents/render_agent/placement/`
- For each archetype, extract the **pure geometry**: a function taking the ordered/structured items + `meta` and returning `{key: {x, y}}`. The shape math (linear / radial / tiered / tree) is identical across levels.
- Provide two thin node-dict wrappers consuming that geometry:
  - **module wrapper:** `id=f"mod__{module_name}"`, `type="moduleSummary"`, `data={label, moduleName, drillable, zoneCount, componentCount}` (preserve current behavior incl. PBI-7 counts).
  - **component wrapper:** `id=<component name>`, `type="custom"`, `data={label, module, isEntry, drillable, tier}` (match `relationship.py`'s node shape).

### 2. Routing — `agents/render_agent/services/placement_service.py`
- Current: `place_key = "module" if view_id.startswith("module:") else template.type`.
- Extend so a `component:*` view routes by `template.type` to the **component-level** wrapper of that archetype; system views keep the module-level wrapper; module views keep the `"module"` (nested-group) placer. Keep edge construction unchanged.

### 3. Edges
- Component-level archetypes must carry their caller/callee/child edges (reuse the existing per-view edge builder; no `mod__` prefix for component views).

## Acceptance criteria
- Each archetype (`pipeline` / `hub_and_spoke` / `hierarchy` / `relationship` / …) renders correctly with **component** nodes (`type="custom"`, component-name ids) and connecting edges.
- Positions are deterministic (identical template → identical coordinates).
- **No regression** to system or module views — same geometry via the module wrapper; counts and nesting intact.

## Out of scope
- Choosing the archetype (PBI 12). This PBI only places whatever `template.type` + `meta` it's given.
- Frontend changes (the node `type`s used here are already registered in `FlowGraph.jsx`).
