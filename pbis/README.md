# PBIs — Diagram Template Library (Layout & Render Agents)

This directory is a work package for an implementing LLM. Read this index first, then execute the PBIs in order. Each PBI file is self-contained but assumes the shared context below. **Obey `CLAUDE.md`** (SOLID, ≤150 lines/file, constructor injection, schemas next to tools, no unsolicited tests, no unsolicited comments/logging, type annotations on all signatures).

## Why this work exists

The layout agent already decides a *system-level* diagram archetype deterministically (`ArchetypeClassifier` → `pipeline | hub | layered | hierarchy | mesh`), but **placement happens in the frontend** (`frontend/src/hooks/graph/*`). Most archetypes get clean deterministic coordinates there; **`mesh` falls through to `positionMesh()` → dagre** (force-directed), producing inconsistent ("random") layouts run-to-run. Separately, the **render agent emits Mermaid that nothing consumes** (`frontend/src/components/MermaidDiagram.jsx` is never imported) — it is dead code.

We fix this by giving each agent one job:

- **Layout agent decides the diagram type.** An LLM picks the template type (it can read what the code does), constrained by a **deterministic** selector tool that enforces per-type node limits, rejects over-limit picks with a structured error + suggested alternative, drives a bounded retry, then falls back to `mesh`.
- **Render agent draws/places.** It consumes the chosen template schema and computes **deterministic** React Flow positions (no dagre), replacing the dead Mermaid path.
- **Frontend renders.** The system-level graph hook becomes a thin pass-through over backend-supplied positions; it only applies theme/styling.

**Outcome:** same repo in → same system diagram out, every run.

## Not the old `shared/templates/*.json`

`PROMPT.md` notes the project deliberately deleted five JSON templates that *forced every repo into one flat 3-band layout*. **These templates are different and do not reintroduce that.** Here a "template" is a **placement algorithm chosen per repo** based on that repo's actual module graph; selection is deterministically validated against node limits and falls back safely. Nothing forces a uniform layout, there are no embeddings/vector DBs, and the facts-vs-interpretation principle holds: the LLM only *picks a type*; limits, rejection, fallback, and placement math are deterministic.

## Locked decisions

1. **Templates are code, not SVG.** Each template = a Python *definition* (limits/fields/description) + a *placement function*, both registered in registries. The unfinished `agents/layout_agent/diagram_templates/*.svg` mockups are removed.
2. **Scope = system-level diagram only** (the module graph). Module drill-down/component views are already deterministic (`cluster_plan` + `clusterLayout.js`) and are left unchanged.
3. **LLM picks the type; validation/limits/rejection/fallback are deterministic.** Temperature stays 0.
4. **Type set this batch:** `pipeline`, `hub_and_spoke`, `layered_tier`, `hierarchy`, `mesh`, `dependency_graph`. (`sequence`, `state_machine`, `event_flow` are deferred drop-ins.)
5. **Render agent → React Flow JSON replaces Mermaid.** Frontend wiring is explicitly authorized for this batch (overrides the usual "don't touch frontend" rule).
6. **Backend/frontend contract:** backend supplies *structure + positions* only (`id`, `type`, `position{x,y}`, `data{}`; edges `{source, target, edge_type, label?}`). Frontend keeps *theme/styling* (colors, markers) via existing helpers (`colorForModule`, `toRFEdge` in `frontend/src/hooks/graph/common.js`).

## Canonical template schema (the extensibility mechanism)

One shape across all types; type-specific data rides in `meta` so the renderer never needs rewriting when a type is added:

```
DiagramTemplate:
  type:  DiagramType                # pipeline | hub_and_spoke | layered_tier | hierarchy | mesh | dependency_graph
  nodes: [TemplateNode]             # ordered; ordering semantics defined per type
  edges: [TemplateEdge]             # {source, target, edge_type}
  meta:  dict                       # type-specific; each placement fn unpacks its own keys
```

`meta` per type: `hub_and_spoke` → hub node id; `layered_tier` → tier index per node; `hierarchy` → parent/depth per node; `pipeline`/`mesh`/`dependency_graph` → ordering only. Future `sequence` → actor order; `state_machine` → transition labels. Nodes/edges stay generic; only `meta` keys differ.

## Execution order & dependencies

### Phase 1 — system-level template path (DONE ✅, verified on disk)

| PBI | Title | Depends on |
|-----|-------|------------|
| [1](pbi-1-template-schema-registry.md) | Template schema, definitions, registry, limits config | — |
| [2](pbi-2-selector-tool.md) | Deterministic selector tool `select_diagram_template` | 1 |
| [3](pbi-3-llm-selection-loop.md) | LLM-driven selection loop in layout agent | 2 |
| [4](pbi-4-render-placement-engine.md) | Render agent placement engine (template → React Flow JSON) | 1 |
| [5](pbi-5-orchestration-wiring.md) | Orchestration & client wiring (API gateway) | 3, 4 |
| [6](pbi-6-frontend-thin-renderer.md) | Frontend thin renderer | 5 |

PBIs 1→2→3 (layout) and 1→4 (render) ran in parallel after PBI 1; PBI 5 joined them; PBI 6 last. All complete.

### Phase 2 — templates at EVERY level (system + module + component)

Phase 1 templated only the system view, which is edge-sparse (all traced edges are intra-module → module-summary view has nothing to connect). Phase 2 pushes the template library down every navigable level, where the real graph and edges live. Decisions: **backend owns all placement**, **type selection folds into the existing per-module LLM call (~0 added cost)**, **delivery is a precomputed view map** `{viewId → {type, nodes, edges}}`, format stays **React Flow JSON**.

| PBI | Title | Depends on |
|-----|-------|------------|
| [7](pbi-7-multiview-schema-contract.md) | Multi-view template schema + view-map contract | Phase 1 |
| [8](pbi-8-layout-per-view-specs.md) | Layout agent: build a template spec per view (fold-in type selection) | 7 |
| [9](pbi-9-render-multilevel-placement.md) | Render agent: placement for module + component views | 7, 8 |
| [10](pbi-10-frontend-consume-viewmap.md) | Frontend: consume the view map; retire client-side placement | 9 |

Run 7 → 8 → 9 → 10 in order. (Phase 2 done — verified in live output.)

### Phase 3 — recursive drill-down + component-level templates

Phase 2 templated all three levels, but live testing (diagnosed by three subagents) found the component level: (a) **blanks** when you drill into a nested child — `ViewPlanner` only creates views for non-nested components, so nested children are drillable-but-viewless; and (b) **bypasses the template library** — the component view hardcodes a `relationship` fan layout instead of selecting a type. Decisions: **full recursive drill-down** (views for every component with children/relationships, incl. nested; trivial leaves non-drillable) and **deterministic component-level archetype selection** (Option B — classify each component's local graph; `relationship` becomes the formalized fallback; no per-component LLM call).

| PBI | Title | Depends on |
|-----|-------|------------|
| [11](pbi-11-recursive-component-views.md) | Recursive component views + drillability correctness | Phase 2 |
| [12](pbi-12-component-archetype-classifier.md) | Component-level archetype classifier + selection (layout) | 11 |
| [13](pbi-13-generalize-archetype-placement.md) | Generalize archetype placement to component nodes (render) | 7 |

Run 11 first (independent; fixes the blank page, keeps current look). Then 12 + 13 together — 12 sets `type`+`meta`, 13 places it; contract is `template.type` + `meta`. See the master plan for full context: `~/.claude/plans/goal-refactor-the-layout-cheerful-allen.md`.

## End-to-end verification

1. **Determinism:** run `/analyse` twice on the same repo; assert identical system-view node positions and identical chosen template type.
2. **Limit/rejection path:** feed a spec exceeding a type's limit (e.g. 15 modules forced to `hub_and_spoke`); confirm structured rejection, bounded retry, valid fallback (`mesh`) — never a crash, never silent truncation (check logs).
3. **Each type renders:** minimal specs classifying to each of the 6 types → render agent returns sane non-overlapping positions for each.
4. **Frontend:** load a mesh-heavy repo; system graph stable on reload; drill-down/component views unaffected.
5. **Dead-path removal:** no remaining references to `MermaidService` / `MermaidDiagram.jsx` / dagre in the system path.

## Reference: current code touchpoints

- Layout pipeline: `agents/layout_agent/routers/layout.py`, `dependencies.py`, `services/*`, `helpers/archetype_classifier.py`, `helpers/module_graph.py`
- Tool pattern to copy: `agents/profiler_agent/tools/get_file_tree_tool.py`
- Structured-result pattern to copy: `agents/tracer_agent/services/graph_validator.py` (`ValidationResult`)
- Render agent: `agents/render_agent/{routers/render.py,dependencies.py,models/render_model.py,services/mermaid_service.py}`
- Orchestration: `api/services/analysis_service.py`, `api/clients/render_client.py`, `api/models/analysis_model.py`
- Frontend: `frontend/src/hooks/useGraphTransform.js`, `frontend/src/hooks/graph/{systemGraph,common}.js`, `frontend/src/components/diagram/{FlowGraph,DiagramExplorer}.jsx`, `frontend/src/pages/DiagramPage.jsx`
- Shared models: `shared/models/diagram_spec.py`
