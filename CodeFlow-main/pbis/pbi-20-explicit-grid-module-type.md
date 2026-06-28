# PBI 20 — Explicit `zoned` (grid) module type + type-appropriate module template (layout)

**Batch:** 5 &nbsp;|&nbsp; **Depends on:** — &nbsp;|&nbsp; **Read `README.md` first.**

## Why
At the module level the chosen `diagram_type` is currently cosmetic: the renderer ignores it (see
PBI 21) and the zone grid is forced on every module. We want the zone grid to be a **first-class,
optional** template the selector can deliberately choose for a runnable unit with clean zones, while
structural modules reshape by their type. This PBI is the layout half: make the grid a real type and
emit a module template whose node shape matches the chosen type so the renderer can place it.

## Scope

### 1. Type — `shared/models/diagram_template.py`
Add a module-level diagram type for the zone layout. Name it **`zoned`** (NOT `grid`) to avoid
colliding with the existing cluster-level `style="grid"`. This is the "grid" concept the user
described. `zoned` is **module-only** — modules have zones, components do not — so component-level
selection is untouched.

### 2. Selection — `agents/layout_agent/prompts/cluster_prompt.py`
Add `zoned` to the allowed `diagram_type` values with guidance, e.g.: *"zoned": a runnable unit with
clean zones (data / business / tools) and no single dominant flow — keep the components grouped by
zone. Otherwise pick the structural type (pipeline / hub_and_spoke / hierarchy / layered_tier) that
fits.* Keep temperature 0; keep the strict-JSON contract.

### 3. Validation — `agents/layout_agent/helpers/cluster_validator.py`
Accept `zoned` wherever `diagram_type` is validated/parsed (and any `_parse_type` helper in
`services/cluster_planner.py`).

### 4. Template build — `agents/layout_agent/services/_view_builder.py:build_module`
Branch on `diagram_type`:
- **`zoned`** → today's zone → cluster → component hierarchy (unchanged behaviour).
- **structural types** (`hub_and_spoke`, `pipeline`, `hierarchy`, `layered_tier`) → a **flat list of
  the module's primary components** as `kind="component"` nodes (no zone/cluster parents), keep the
  intra-module edges, and populate `meta` with what the structural placements need:
  `hub_id` = the highest-fan-out component (compute from the module edges), and `depth_map` via BFS
  over those edges (matching what the system-level `hierarchy`/`hub_and_spoke` placements read).

## Acceptance criteria
- The cluster planner can choose `zoned`, and it validates.
- A structural module template carries flat `component` nodes + a populated `meta` (`hub_id`,
  `depth_map`); a `zoned` module template keeps the zone/cluster hierarchy.
- Selection remains deterministic at temperature 0.

## Out of scope
- The render-side dispatch and placement (PBI 21).
- Changing the component-level archetype classifier or de-biasing selection.
