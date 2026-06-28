# PBI 3 — LLM-driven template selection loop

**Depends on:** PBI 2. **Read `README.md` first.**

## Why
The LLM chooses the diagram type from real understanding of the code, while the deterministic selector (PBI 2) keeps it inside the rails. This is the "layout agent decides the diagram type" half of the design.

## Scope

### 1. Prompt — `agents/layout_agent/prompts/template_prompt.py` (new)
System prompt that instructs the LLM to choose exactly one `DiagramType` and call `select_diagram_template`. Provide in the user/evidence message:
- compact spec evidence (modules, module-level edges, entry points),
- the `ArchetypeClassifier` result as a **hint** (not a command),
- the registry `descriptions()` (type, description, limit).
Temperature 0. Keep the prompt deterministic in phrasing.

### 2. Planner service — `agents/layout_agent/services/template_planner.py` (new)
`TemplatePlanner`, constructor-injected with `anthropic.AsyncAnthropic` (as in existing `dependencies.py`), the `SelectDiagramTemplateTool` (PBI 2), the `ArchetypeClassifier`, and the `TemplateRegistry`. One public method, e.g. `async def plan(spec: DiagramSpec) -> DiagramTemplate`:
- Run an Anthropic **tool-use loop**: the model emits a `tool_use` for `select_diagram_template`; execute it via the tool; feed the `tool_result` back.
- On a **rejection** result, allow the model to retry — **max 2 retries** — by either (a) re-picking the `suggested_type`, or (b) requesting promotion of only **primary-tier** components (tier is already on `Component`, set by `SemanticLayoutService`) to shrink the node set, then re-validating.
- After 2 failed retries → **deterministic fallback**: call the selector with `type="mesh"` and use that template.
- `logger.info(...)` the decision trail (each attempted type, each rejection, final chosen type + node count).

> Reuse whatever tool-use loop helper the repo already has if present; otherwise implement a minimal loop inline in the service (still ≤150 lines — split a helper if needed).

### 3. Response model — `agents/layout_agent/models/layout_model.py`
Add `diagram_template: DiagramTemplate` to `LayoutResponse`.

### 4. Router — `agents/layout_agent/routers/layout.py`
After `semantic.enrich(...)` and `cluster_planner.plan(...)`, call `template_planner.plan(spec)` and attach the result to `LayoutResponse`. Inject the planner via `Depends(get_template_planner)`.

### 5. DI — `agents/layout_agent/dependencies.py`
Add `get_template_planner(...)`.

## Acceptance criteria
- Valid first pick → that template is returned.
- Over-limit first pick → bounded retry → a valid template or the `mesh` fallback; **never crashes**, always returns a usable `DiagramTemplate`.
- Retry count is hard-capped at 2; logs show the full decision trail.
- Selection is repeatable on a fixed spec at temperature 0.

## Out of scope
- Placement/positions (PBI 4). The planner returns a `DiagramTemplate` with structure + `meta`, not coordinates.
