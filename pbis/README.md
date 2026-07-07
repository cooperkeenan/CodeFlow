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

### Phase 4 — unbiased selection, recovered edges, reasoning telemetry

Live diagnosis: the layout agent picked `hub_and_spoke` for nearly every view because (a) the system
module-graph has **zero cross-module edges** — all traced edges are intra-module, so the selector
chooses a type for an edgeless graph; (b) a deterministic `archetype_hint` primes the choice; and
(c) nothing records *why* a type was chosen. Fix: recover the real cross-service edges, remove the
hint, lean on richer descriptions, and log the agent's reasoning to both a file and a per-view UI box.

**This is Batch 4** — one self-contained handoff of PBIs 14–19. Hand the whole batch to the
implementing agent ("execute Batch 4 / the next batch of PBIs"); it implements all six. The
`Depends on` column is *internal* run-order within the batch, not separate batches.

| PBI | Title | Depends on |
|-----|-------|------------|
| [14](pbi-14-unbias-template-selection.md) | Unbias system template selection | — |
| [15](pbi-15-recover-cross-service-edges.md) | Recover cross-service HTTP edges (tracer) | — |
| [16](pbi-16-relationship-aware-descriptions.md) | Relationship-aware module descriptions | 15 |
| [17](pbi-17-capture-selection-reasoning.md) | Capture selection reasoning into meta + logs | 14 |
| [18](pbi-18-persist-reasoning-file.md) | Persist a readable reasoning file (api) | 17 |
| [19](pbi-19-frontend-rationale-box.md) | Per-view rationale box (frontend) | 17 |

Suggested internal order: **14, 15 → 16 → 17 → 18, 19**. (14 + 15 are independent foundations; 16
builds on 15; 18 + 19 both consume the `meta["rationale"]` from 17.)

**Phase 4 verification:** `/analyse` this repo and assert (1) `diagram_spec.edges` has ≥1
cross-module edge; (2) `shared/outputs/layout_reasoning.json` exists with a per-view `type` +
`rationale`; (3) two runs give identical types + rationale (temperature 0); (4) the UI shows a
`RationaleBox` per view; (5) intra-module `call` edges and placement (`layout_hint`) are unchanged,
no new `W3` warnings.

### Phase 5 — type-driven module rendering (+ explicit grid) and a structural answer-sheet

Live review of Batch 4's output found two things: (a) the `diagram_type` is **cosmetic at the module
level** — `render_agent/services/placement_service.py` hardcodes the zone grid regardless of
`template.type`, so every module looks the same; and (b) there's no automated way to measure a run.
Batch 5 makes module placement honor the type, adds the zone grid as a **first-class, optional**
`zoned` template the selector can deliberately choose for runnable units, and adds an automated
**structural answer-sheet** (ground truth authored from source) with a scorecard CLI. The
component-level hub classifier is intentionally left alone this round — measure first, then de-bias.

**This is Batch 5** — one self-contained handoff of PBIs 20–23 (run `python -m evaluation.compare`
after `/analyse` to score a run).

| PBI | Title | Depends on |
|-----|-------|------------|
| [20](pbi-20-explicit-grid-module-type.md) | Explicit `zoned` (grid) module type + type-appropriate template (layout) | — |
| [21](pbi-21-module-placement-by-type.md) | Module placement honors the diagram type (render) | 20 |
| [22](pbi-22-answer-sheet-fixture.md) | CodeFlow structural answer-sheet fixture | — |
| [23](pbi-23-comparison-harness.md) | Structural comparison harness + scorecard CLI | 22 |

Suggested internal order: **20 → 21** and **22 → 23** (the two themes are independent). `zoned` is
module-only and named distinctly from the cluster-level `style="grid"`.

### Phase 6 — description-driven component type selection

Live review found component views are typed from **call-graph topology only**
(`helpers/component_archetype_classifier.py:19`): every orchestrator (≥3 callees) becomes
`hub_and_spoke`, and `pipeline` only fires for a single callee. So `TracerService` — which runs its
six helpers in sequence — renders as a hub even though it's a pipeline. The ordering/semantics that
make it a pipeline aren't in the data. Batch 6 has the tracer emit a rich purpose description (with
ordered steps) per high-level component, and the layout agent make **one batched LLM call** to pick
the type (and, for sequential types, the node order) from those descriptions. Leaf components stay
on the deterministic classifier.

**This is Batch 6** — one self-contained handoff of PBIs 24–25.

| PBI | Title | Depends on |
|-----|-------|------------|
| [24](pbi-24-tracer-highlevel-descriptions.md) | Rich purpose descriptions for high-level components (tracer) | — |
| [25](pbi-25-llm-component-type-selection.md) | Description-driven component template selection (layout) | 24 |

Run **24 → 25**. Reuses the `meta["rationale"]` + `RationaleBox` plumbing (Batch 4) and the
`component_<type>` placements (Batch 5) — no render changes.

### Phase 7 — type-aware edges ("real" templates)

Batch 6 typed `TracerService` as `pipeline` and ordered its nodes, but the **edges stayed the raw
star** (`TracerService → each helper`; `meta.order` was `None`) — so dragging the boxes still shows a
hub. Root cause: edges are **type-agnostic** (`placement_service._build_edges` passes
`template.edges` through 1:1; layout builds the same call edges regardless of type), so only node
*positions* change per type. Batch 7 makes each template own **edges that match its type**: pipeline
= `caller→orchestrator→step1→…→stepN`, hierarchy = parent→child tree, layered_tier = cross-tier; hub
/ mesh / dependency_graph keep their current (correct) edges. Synthesized sequence edges are styled
distinctly from literal calls.

**This is Batch 7** — one self-contained handoff of PBIs 26–27.

| PBI | Title | Depends on |
|-----|-------|------------|
| [26](pbi-26-type-aware-edges.md) | Type-aware edge construction in templates (layout) | — |
| [27](pbi-27-render-honor-type-edges.md) | Render honors per-type meta + distinguishes flow edges | 26 |

Run **26 → 27**. PBI 26 also fixes the Batch 6 `meta.order = None` gap so the sequence is captured. (Batch 7 done ✅)

### Phase 8 — pipeline layout polish

| PBI | Title | Depends on |
|-----|-------|------------|
| [28](pbi-28-pipeline-side-handles.md) | Pipeline edges route into node sides (frontend) | — |
| [29](pbi-29-system-view-ordered-chain.md) | System view honors type-aware edges (ordered chain) | — |

Run **28 + 29** (independent). (Batch 8 done ✅)

### Phase 9 — regression fix: component-type selector hardening + module pipeline de-bias

| PBI | Title | Depends on |
|-----|-------|------------|
| [30](pbi-30-harden-component-selector.md) | Harden component-type selector (no silent total fallback) | — |
| [31](pbi-31-module-pipeline-selection.md) | Let module views be pipelines (de-bias cluster planner) | — |

Run **30 + 31** (independent). (Batch 9 done ✅)

### Phase 8 — pipeline layout polish

After Batch 7, component pipelines chain correctly but (a) the arrows route through top/bottom
handles so a horizontal pipeline looks messy, and (b) the **system view** is typed `pipeline` yet
still shows alphabetical nodes + `api→each` hub edges — because the system template is built on the
`TemplatePlanner` path, not the Batch 7 `_edge_builder`. Batch 8 routes pipeline arrows into the
sides and gives the system view the same ordered chain (by `layout_hint.module_order`).

**Batch 8** — PBIs 28–29.

| PBI | Title | Depends on |
|-----|-------|------------|
| [28](pbi-28-pipeline-side-handles.md) | Pipeline edges route into the sides (frontend) | — |
| [29](pbi-29-system-view-ordered-chain.md) | System view honors type-aware edges (ordered chain) | — |

### Phase 9 — fix the silent component-selector regression + module pipelines

Live test of Batch 8 showed **everything reverted to `hub_and_spoke`**: `component:TracerService`
went pipeline → hub with `rationale: None`, and 0 of 47 component views had a rationale. Root cause:
the Batch 6 `ComponentTypePlanner` makes **one batched LLM call, all-or-nothing**, with
`max_tokens=4000`; the richer descriptions overflow it, the JSON fails to parse, and `plan()` silently
`return {}` — so the whole component layer falls back to the deterministic topology classifier (≥3
callees → hub). Batch 9 hardens it (chunk / raise tokens / keep partial results / surface failures)
and applies the same semantics-over-topology fix at the **module** level so a sequential orchestrator
module can be a pipeline instead of auto-hub on fan-out.

**Batch 9** — PBIs 30–31.

| PBI | Title | Depends on |
|-----|-------|------------|
| [30](pbi-30-harden-component-selector.md) | Harden the component-type selector (no silent total fallback) | — |
| [31](pbi-31-module-pipeline-selection.md) | Let module views be pipelines (de-bias the cluster planner) | — |

### Phase 10 — service-centric abstraction + container drill-down

Higher-level pipelines surface thin adapter/tool nodes (`BuildCallGraphTool`) instead of the
meaningful services (`CallGraphService`). Batch 10 surfaces **primary roles** (service / orchestrator /
repository) and deterministically **folds single-callee adapters** (tool/client/helper) into the
service they wrap, so the high-level view reads `TracerService → CallGraphService → EvidenceService →
…`. Drilling into a service opens a **container** holding the folded tool + service + helpers, with
the caller feeding in (per the figma mockup). Role-based (generic across `*Service`/`*Manager`/…),
deterministic contraction; ordering reuses the Batch 6/7 sequence. Reuses the `zoned` group-node
rendering for containers.

**Batch 10** — PBIs 32–33.

| PBI | Title | Depends on |
|-----|-------|------------|
| [32](pbi-32-service-surfacing-contraction.md) | Role-based service surfacing + adapter contraction (layout) | Batch 7 |
| [33](pbi-33-service-container-drilldown.md) | Container drill-down for a folded service (layout + render) | 32 |

Run **Batch 9 (30, 31)** first — it fixes the live regression — then **Batch 10 (32 → 33)**.

### Phase 11 — click-to-view-code (Neon-backed source viewer)

A diagram component never shows its **source code**. Batch 11 adds a masthead **"code view"
toggle**: while on, clicking a code-backed component shows that file's source in a side
panel, auto-scrolled to / highlighting the component's definition, and clicking another
component swaps it automatically. The click→file linkage needs **no** layout/render change —
every `Component` already carries `file_path` and the full `diagram_spec` already reaches the
frontend. What's missing is captured **line ranges** (deterministic from the AST) and a place
to read source from at view time: source is currently fetched to a temp dir and discarded, so
we persist each analyzed file to **Neon (Postgres)**, deduped by content hash.

**Batch 11** — PBIs 34–37.

| PBI | Title | Depends on |
|-----|-------|------------|
| [34](pbi-34-component-line-ranges.md) | Capture component source line ranges (tracer) | — |
| [35](pbi-35-neon-code-store.md) | Neon code store + source persistence (tracer) | — |
| [36](pbi-36-code-serving-endpoint.md) | Code-serving endpoint `GET /code` (api) | 35 |
| [37](pbi-37-frontend-code-view.md) | Frontend: code-view toggle + code panel | 34, 36 |

Suggested internal order: **34 + 35** (independent tracer foundations) → **36** → **37**.
Frontend changes are authorized for PBI 37. Requires a Neon DB with `DATABASE_URL` set in
`.env`. Master plan: `~/.claude/plans/snuggly-growing-kay.md`.

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
