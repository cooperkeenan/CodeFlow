# PBI 2 — Deterministic selector tool (`select_diagram_template`)

**Depends on:** PBI 1. **Read `README.md` first.**

## Why
This is the deterministic guardrail around the LLM's type choice. Given a candidate type and the spec, it either builds a valid `DiagramTemplate` or returns a structured, machine-readable rejection with a suggested alternative. The LLM (PBI 3) never bypasses these rules.

## Scope

### 1. Service — `agents/layout_agent/services/template_selector_service.py` (new)
`TemplateSelectorService`, constructor-injected with `TemplateRegistry` (PBI 1), the limits config, and `ModuleGraphBuilder` (`helpers/module_graph.py`) for counts/depth. One public method, e.g. `select(diagram_type: DiagramType, spec: DiagramSpec) -> SelectionResult`:
- Build the module graph; count nodes (modules) and, for `hierarchy`, compute depth.
- **Within limit →** build a `DiagramTemplate`:
  - map modules → `nodes` in the type's canonical order (pipeline = `module_order`; hub_and_spoke = hub first then spokes; layered_tier = by rank/tier; hierarchy = parent→children; mesh/dependency_graph = stable sorted),
  - carry `edges` (aggregated module-level edges, reuse the aggregation logic mirrored from frontend `systemGraph.js`),
  - fill `meta` per type (hub id; tier indices; parent/depth map).
- **Over limit →** return a structured rejection (see dataclass below); do not build a template.

### 2. Structured result — follow `ValidationResult` style in `agents/tracer_agent/services/graph_validator.py`
A dataclass, e.g.:
```
SelectionResult:
  ok: bool
  template: DiagramTemplate | None
  limit_hit: str | None        # e.g. "hub_and_spoke.node_limit"
  actual_count: int | None
  suggested_type: DiagramType | None
```
Suggestion rule (deterministic): over hub/pipeline/layered/hierarchy limit → suggest `dependency_graph`; over `dependency_graph` → suggest `mesh`. `mesh` is the terminal fallback.

### 3. Mesh fallback / no silent truncation
- `mesh` accepts up to its limit. If even `mesh` overflows, **still build it** (do not truncate silently) and `logger.warning(...)` the overflow with the actual count.

### 4. Tool — `agents/layout_agent/tools/select_diagram_template_tool.py` (new)
Follow the pattern in `agents/profiler_agent/tools/get_file_tree_tool.py`:
- `SELECT_DIAGRAM_TEMPLATE_SCHEMA` (Anthropic tool schema) **in the same file**; input = `{ "diagram_type": <enum of the 6 types> }` (the spec is held by the service, not passed by the LLM).
- `SelectDiagramTemplateTool` with `__init__(self, service: TemplateSelectorService)` and `async def handle(self, tool_input: dict) -> str` that wraps exactly one service call and returns JSON — either the serialized `DiagramTemplate` or the serialized rejection. No logic in the handler beyond serialization/error capture.
- Errors/rejections logged via `logging.getLogger(__name__)`.

### 5. Wire into DI — `agents/layout_agent/dependencies.py`
Add `get_template_selector_service()` and `get_select_diagram_template_tool()`.

## Acceptance criteria
- Over-limit pick returns a rejection naming the limit, the actual count, and a viable `suggested_type`.
- Same `(diagram_type, spec)` always yields byte-identical output (pure/deterministic).
- A valid pick returns a `DiagramTemplate` whose `meta` contains exactly the type's `required_meta` keys.
- Tool handler contains no business logic (delegates to the service).

## Out of scope
- Deciding *which* type to try (PBI 3). The service is told the type and only validates/builds.
