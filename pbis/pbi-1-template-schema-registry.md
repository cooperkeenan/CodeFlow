# PBI 1 — Template schema, definitions, registry, and limits config

**Depends on:** none. **Read `README.md` first** (schema + decisions).

## Why
Foundation for every other PBI. Defines the canonical, extendable `DiagramTemplate` shape, the per-type definitions/limits, and removes the SVG mockups. Done right, adding a new diagram type later is a one-file change.

## Scope

### 1. Shared model — `shared/models/diagram_template.py` (new)
- `DiagramType = Literal["pipeline", "hub_and_spoke", "layered_tier", "hierarchy", "mesh", "dependency_graph"]`.
- `TemplateNode` (Pydantic): at minimum `id: str`, `label: str`, plus structural fields needed by placement (e.g. `tier: ComponentTier` reuse, `module_name`). Keep it minimal and generic.
- `TemplateEdge` (Pydantic): `source: str`, `target: str`, `edge_type: EdgeType` (reuse `EdgeType` from `diagram_spec.py`).
- `DiagramTemplate` (Pydantic): `type: DiagramType`, `nodes: list[TemplateNode]`, `edges: list[TemplateEdge]`, `meta: dict = {}`.
- Type-specific data goes only in `meta` (see README). Do **not** add per-type fields to the top-level model.

### 2. Template definitions — `agents/layout_agent/templates/` (new package, one file per type)
Six files (`pipeline.py`, `hub_and_spoke.py`, `layered_tier.py`, `hierarchy.py`, `mesh.py`, `dependency_graph.py`). Each exposes a definition dataclass with:
- `type: DiagramType`
- `node_limit: int` (and `max_depth: int | None` where relevant, e.g. `hierarchy`)
- `required_meta: tuple[str, ...]` / `optional_meta: tuple[str, ...]` — names of `meta` keys the placement function will read
- `description: str` — one line, used to help the LLM choose (PBI 3)

Definitions are pure data — no placement logic here (placement lives in the render agent, PBI 4).

### 3. Registry — `agents/layout_agent/templates/registry.py` (new)
`TemplateRegistry` exposing:
- `get(type) -> definition`
- `descriptions() -> list[tuple[DiagramType, str, int]]` (type, description, limit) for prompt building
- `types() -> list[DiagramType]` (canonical order)
Construct it from the six definitions via constructor injection / a simple factory in `dependencies.py`.

### 4. Limits config — extend `agents/layout_agent/core/config.py` (or sibling `template_config.py`)
- Per-type limits as config defaults (overridable, not hardcoded in logic): `pipeline=8`, `hub_and_spoke=8`, `mesh=12`, `hierarchy` `max_depth=3`, and sensible defaults for `layered_tier` and `dependency_graph`.
- The definition dataclasses read their limits from this config (inject it), so changing a limit needs no logic edit.
- **Leave `MAX_HUB_SPOKES` / `MAX_HIERARCHY_CHILDREN` in `helpers/cluster_validator.py` untouched** — those are cluster-level (module-interior) and a separate concern.

### 5. Remove SVG
- Delete `agents/layout_agent/diagram_templates/*.svg` and the now-empty directory.

## Acceptance criteria
- A new type can be added by creating one definition file and registering it — no change to `DiagramTemplate`.
- Per-type limits are read from config; changing one is a config-only edit.
- `DiagramTemplate` round-trips through Pydantic (serialize → JSON → deserialize) cleanly.
- No SVG files remain under `agents/layout_agent/`.
- Backend imports cleanly.

## Out of scope
- Placement math (PBI 4), the selector tool (PBI 2), any LLM wiring (PBI 3).
