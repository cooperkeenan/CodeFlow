# PBI 7 — Multi-view template schema + view-map contract

**Phase:** 2 (templates at every level). **Depends on:** Phase 1 (PBIs 1–6, done). **Read `README.md` first.**

## Why
The Phase 1 `DiagramTemplate` is flat and single-view — it can only describe the system overview. To template every level we need (a) per-view delivery and (b) node nesting so a module view can express zones → clusters → components. Verified problem: the new template path covers only the sparsest level (module boxes), and the system view has no edges because all 43 traced edges are intra-module (the real graph lives inside modules).

## Scope

### 1. Extend `shared/models/diagram_template.py`
- `TemplateNode` gains:
  - `kind: Literal["module", "component", "zone", "cluster"] = "module"`
  - `parent: str | None = None` (id of the containing group node)
  - `style: str | None = None` (cluster layout style: grid/stack/pipeline/hierarchy/hub — reuse `LayoutStyle` values)
  - keep existing `id`, `label`, `tier`, `module_name`.
- Add `"relationship"` to the type literal used for views (component view), or introduce a `DiagramView` model with `type: DiagramType | Literal["relationship"]`, `nodes: list[TemplateNode]`, `edges: list[TemplateEdge]`, `meta: dict = {}`. Prefer reusing `DiagramTemplate` and widening its `type` if that stays ≤150 lines and clean.

### 2. View-map contract
- `viewId` scheme (string keys): `"system"`, `"module:<moduleName>"`, `"component:<componentName>"`.
- Layout side produces `dict[str, DiagramTemplate]` (structure + chosen type + meta per view).
- Render side produces `dict[str, RenderedView]` where `RenderedView = {type: str, nodes: list[dict], edges: list[dict]}` (plain React Flow JSON).

### 3. Update transport models
- `agents/render_agent/models/render_model.py`: `RenderRequest.diagram_templates: dict[str, DiagramTemplate]`; `RenderResponse.views: dict[str, RenderedView]`.
- `api/models/analysis_model.py`: `AnalyseResponse` carries `diagram: {"views": dict[str, RenderedView]}` — replace the single-graph/`mermaid` field.

## Acceptance criteria
- `DiagramTemplate`/`TemplateNode` round-trip through Pydantic with nesting fields populated.
- A `parent`/`kind`/`style` set on nodes serializes and deserializes cleanly.
- Transport models accept and return the view-map dict shape.
- Adding a new view kind or node kind requires no change to the transport plumbing (only to producers/placers).

## Out of scope
- Producing the per-view specs (PBI 8) and placing them (PBI 9).
