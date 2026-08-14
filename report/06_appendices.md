# 06 — Appendices

Reference material for the dissertation's appendices. Everything here is quoted verbatim from the
repository at commit `b9779cf` plus the working tree.

---

## Appendix A — `FlowGraph` (the live pipeline contract)

`shared/models/flow_graph.py`, complete:

```python
NodeKind   = Literal["entry", "step", "decision", "parallel", "effect", "outcome"]
EdgeKind   = Literal["sequence", "arm", "parallel", "stitch"]
Confidence = Literal["resolved", "inferred", "dynamic"]
EffectKind = Literal["http_out", "database", "llm", "file", "queue", "email", "response"]
Badge      = Literal["loop", "recursive", "dynamic", "guarded", "folded"]
BodyKind   = Literal["flow", "list"]

class SourceRef(BaseModel):
    file: str
    line: int
    end_line: int

class FlowNode(BaseModel):
    id: str
    kind: NodeKind
    lane: str
    label: str                              # source-derived
    llm_label: str | None = None            # model-written — never structural
    one_liner: str = ""
    backing: list[str] = []
    refs: list[SourceRef] = []
    badges: list[Badge] = []
    folded_count: int = 0
    effect_kind: EffectKind | None = None
    effect_target: str = ""
    level: int = 0                          # containment depth; 0 = always drawn
    hidden_children: list[str] = []         # exactly what a "+" reveals
    owner_fqn: str = ""
    arm_path: list[str] = []
    containers: list[str] = []              # the containment parent set
    body_kind: BodyKind = "flow"
    body_head: str = ""
    body_tails: list[str] = []

class FlowEdge(BaseModel):
    source: str
    target: str
    kind: EdgeKind
    arm_label: str = ""
    llm_label: str | None = None
    group_id: str = ""
    confidence: Confidence = "resolved"
    is_spine: bool = False
    hidden_path: list[str] = []

class Lane(BaseModel):
    id: str
    name: str
    llm_title: str | None = None
    entry_ids: list[str]
    mass: float

class FlowGraph(BaseModel):
    repo: str
    page_title: str = ""
    lanes: list[Lane]
    nodes: list[FlowNode]
    edges: list[FlowEdge]
    meta: dict = {}

    @model_validator(mode="after")
    def _sort_canonical(self) -> "FlowGraph":
        self.nodes.sort(key=lambda node: node.id)
        self.edges.sort(key=lambda edge: (
            edge.source, edge.target, edge.kind,
            edge.group_id, edge.arm_label, edge.confidence, edge.is_spine,
        ))
        return self
```

**Field derivation.** Only `containers` is authored; `level`, `hidden_children`, `body_kind`,
`body_head` and `body_tails` are all computed from it plus the edge set by `ContainmentIndexer` in
two passes (`_assign_shape`, then `_assign_kind`).

---

## Appendix B — `ProfileResponse` / `RepoBlueprint`

`shared/models/profiler_response.py` is one line: `ProfileResponse = RepoBlueprint`.

```python
class ZonePlan(BaseModel):
    name: str
    description: str = ""
    directories: list[str] = []

class ModulePlan(BaseModel):
    name: str
    description: str = ""
    root_path: str
    style: str = ""
    zones: list[ZonePlan] = []
    is_service: bool = False

class RepoBlueprint(BaseModel):
    architecture_type: str
    language: str
    framework: str
    patterns: list[str] = []
    modules: list[ModulePlan] = []
```

---

## Appendix C — `TracerRequest`, `LayoutResponse`, `RenderResponse`, `RenderedView`

```python
class TracerRequest(BaseModel):
    access_token: str | None = None
    repo_name: str
    local_path: str | None = None
    archive_gz: str | None = None
    architecture_type: str
    language: str
    entry_point_hint: str = ""          # the last vestige of the jarviscg era
    blueprint: RepoBlueprint

class LayoutRequest(BaseModel):  flow_graph: FlowGraph
class LayoutResponse(BaseModel): flow_graph: FlowGraph
class RenderRequest(BaseModel):  flow_graph: FlowGraph
class RenderResponse(BaseModel): view: RenderedView

class RenderedView(BaseModel):
    type: str
    page_title: str = ""
    nodes: list[dict]                   # React Flow node objects, untyped
    edges: list[dict]
    hidden: list[dict] = []
    hidden_edges: list[dict] = []
    node_geometry: dict[str, dict[str, int]] = {}
```

---

## Appendix D — `DiagramSpec` (superseded, retained for two type aliases)

`shared/models/diagram_spec.py`. **Not on the live path.** Included because it is the pre-pivot
contract and the dissertation's evolution narrative refers to it.

```python
EdgeType      = Literal["http", "import", "database", "event", "call", "sequence"]
ComponentTier = Literal["primary", "secondary"]
LayoutStyle   = Literal["grid", "stack", "pipeline", "hierarchy", "hub"]
Archetype     = Literal["pipeline", "hub", "layered", "hierarchy", "mesh"]

class ComponentIO(BaseModel):
    inputs: list[str] = []
    outputs: list[str] = []

class Component(BaseModel):
    name: str
    description: str
    file_path: str
    io: ComponentIO | None = None
    children: list[str] = []
    role: str = ""
    tier: ComponentTier = "primary"
    nested: bool = False
    start_line: int | None = None
    end_line: int | None = None

class Edge(BaseModel):
    source: str
    target: str
    edge_type: EdgeType
    primary: bool = True

class ExternalActor(BaseModel):
    name: str
    type: Literal["database", "api", "webhook", "browser"]
    description: str

class Cluster(BaseModel):
    label: str
    style: LayoutStyle = "grid"
    members: list[str] = []
    children: list["Cluster"] = []

class ZoneClusterPlan(BaseModel):
    zone: str
    clusters: list[Cluster] = []

class Module(BaseModel):
    name: str
    description: str = ""
    root_path: str
    purpose: str = ""
    zones: dict[str, list[Component]] = {}
    cluster_plan: list[ZoneClusterPlan] = []
    is_service: bool = False

class RankAssignment(BaseModel):
    module_name: str
    rank: int

class LayoutHint(BaseModel):
    archetype: Archetype
    module_order: list[str]
    rank_assignments: list[RankAssignment]
    rationale: str = ""

class DiagramSpec(BaseModel):
    architecture_type: str
    modules: list[Module]
    edges: list[Edge]
    external_actors: list[ExternalActor] = []
    entry_points: list[str] = []
    layout_hint: LayoutHint | None = None
```

Note the schema drift: the April 2026 output (`02_decision_algorithm.md` §2.1) grouped components
under `layers` (`presentation` / `business` / `data`). That was replaced by `modules` → `zones` →
`cluster_plan`, removing the hardcoded three-tier assumption — shortly before the file became dead
code entirely.

---

## Appendix E — Tracer analysis models

`agents/tracer_agent/models/` (37 files). The three that define the decision abstraction:

```python
DispatchKind = Literal["branch", "match", "table", "route", "polymorphic", "except", "dynamic"]

@dataclass(frozen=True)
class DispatchSite:
    id: str                          # stable: "{owner_fqn}:{line}"
    owner: str
    kind: DispatchKind
    selector_source: str             # the condition/key/type expression, verbatim
    selector_reads: tuple[str, ...]  # names the selector reads — drives provenance scoring
    arms: tuple[Arm, ...]
    reconverges: bool
    span: SourceRef

Terminal = Literal["returns", "raises", "continues", "falls_through"]

@dataclass(frozen=True)
class Arm:
    index: int
    label_source: str
    callsites: tuple[CallSite, ...]
    terminal: Terminal
    handler_fqn: str | None = None

@dataclass(frozen=True)
class DecisionVerdict:
    verdict: Verdict                 # "decision" | "guarded_step" | "noise"
    question: str
    arm_labels: tuple[str, ...]
    confidence: float
    importance: float
```

---

## Appendix F — Configuration constants

### `significance_config.py` — detection and scoring

```python
@dataclass(frozen=True)
class SignificanceConfig:
    utility_min_fan_in: int = 8         # fan-in above which a component is damped as a utility
    utility_percentile: float = 0.90
    reach_max_depth: int = 6            # bound on transitive reach-set computation
    guard_reach_limit: int = 2          # terminal arm reaching ≤2 components is a guard
    weight_reach: float = 3.0           # × log₂(1 + |live_union|)
    weight_provenance: float = 2.0      # × {0: internal, 1: param, 2: route-reachable param}
    weight_terminal: float = 2.0        # × 1.0 if arms never reconverge
    weight_dispatch_kind: float = 1.0   # × 1.0 if kind ∈ {route, table, polymorphic}
    pillar_hits_iterations: int = 50
    pillar_score_decimals: int = 6      # rounding — required for determinism
```

Introduced at `5874f20` (16 July); the four weights are **unchanged since**. `dd79a6a` (4 August)
added only the two `pillar_*` fields.

### `budget_config.py` — visibility and disclosure

```python
@dataclass(frozen=True)
class BudgetConfig:
    node_budget: int = 40               # was 36 until 3f5cfc8
    max_arms_per_decision: int = 5
    min_lane_nodes: int = 3
    visible_decisions: int = 8
    skeleton_budget: int = 15           # the "max 15 nodes" rule from CLAUDE.md
    max_reveal_per_node: int = 8        # what one "+" may reveal
    seed_anchors_per_lane: int = 3
    max_body: int = 6
```

History: `66a0ab1` (16 Jul) introduced `node_budget=36`, `max_arms_per_decision`, `min_lane_nodes`;
`3f5cfc8` (29 Jul) raised `node_budget` to 40 and added `visible_decisions`; `dd79a6a` (4 Aug) added
the four progressive-disclosure fields.

### Service ports (`api/core/config.py`)

```
Gateway  8000    Profiler 8002    Tracer 8003
Render   8004    Layout   8006    Explain 8007     (8005 unallocated)
```

With `ENVIRONMENT=local` these point at `localhost`; otherwise at Railway.

### Required environment (`.env` — no `.env.example` exists)

```
ANTHROPIC_API_KEY=...
DATABASE_URL=...              # Neon Postgres
LOCAL_REPO_PATH=...           # standing demo target: django-helpdesk
ENVIRONMENT=local
<GitHub OAuth client id/secret>
```

`.env` is not hot-reloaded — the gateway must be restarted after editing. Gateway→tracer and
gateway→layout timeouts are 900 s.

### Model configuration

```python
_MODEL      = "claude-haiku-4-5-20251001"   # llm_decision_judge.py
_BATCH_SIZE = 20                            # candidates per call
temperature = 0                             # every LLM call in the system
max_tokens  = 4000                          # decision judge
```

Caches (`.cache/`): `decision_verdicts.json`, `node_names.json`, `review_findings.json`,
`stitch_verdicts.json`. All content-addressed and keyed on a `PROMPT_VERSION` which must be bumped
manually when a prompt changes.

---

## Appendix G — Prompt templates (verbatim)

Five prompts, 447 lines total across `agents/*/prompts/`. The two that matter most are reproduced
in full; the rest are cited by location.

### G.1 Decision judge — `agents/tracer_agent/prompts/decision_judge_prompt.py` (`PROMPT_VERSION = "2"`)

The single most important prompt in the system: it decides which forks become nodes.

```
You judge whether a fork in Python source is a DECISION a human would put on a mental-model
diagram of the system.

A DECISION is a branch point where the program chooses between genuinely different courses of
action that a reader would need to know about to understand what the system does. Examples:
choosing which service/handler/strategy to use, granting vs denying access, selecting a data
source, routing work down materially different paths.

NOT a decision (these are "guard" or "noise"):
- null/None checks, empty-collection checks, hasattr/isinstance defensiveness
- early returns and raises that only validate input
- logging, telemetry, formatting, string building, serialization branches
- caching hits/misses, retry and error handling
- trivial defaulting (x = a if a else b)

For every decision, also rate "importance": 0.0-1.0, how central this decision is to
understanding what the system does. Rank high: routing between services/agents/strategies,
access and permission decisions, choosing which data source to read from. Rank low: error
handling, retries and fallbacks — even when they are a genuine decision, they are not central
to the mental model. Non-decisions ("guard"/"noise") should get importance 0.0.

Return STRICT JSON only: {"verdicts":[{"id":"<id>","verdict":"decision|guard|noise",
"question":"<the question a human would ask, 2-6 words, only if decision>","arm_labels":["..."],
"confidence":0.0-1.0,"importance":0.0-1.0}]}
"question" must read like a question on a flowchart, e.g. "Service principal allowed?",
"Which data source?".
```

Evidence sent per candidate (`build_decision_evidence`): `id`, `where` (`file:line`), `kind`,
`enclosing_function`, `arm_reach_sizes`, and `source` — a snippet capped at 25 lines.

### G.2 Profiler — `agents/profiler_agent/prompts/profiler_prompt.py`

Note the constraint in the second paragraph, which is the same "the LLM only labels" principle
applied one stage earlier:

```
You are a software architecture expert.

You are given a FIXED module/directory skeleton that was extracted deterministically from a
repository, plus the contents of its dependency/manifest files. Your only job is to LABEL it.

You must NOT invent, remove, rename, merge, or move modules or directories. Every directory you
reference must be copied verbatim from the skeleton. Use the module root_path values verbatim.

For each module, group its directories into zones that reflect their architectural role, and give
each zone a short lowercase label. ...

Return ONLY valid JSON with no markdown fences, no explanation, no preamble, matching this schema:
{ "architecture_type": ..., "language": ..., "framework": ..., "patterns": [...],
  "modules": [ { "name": ..., "root_path": ..., "description": ..., "style": ...,
                 "zones": [ { "name": ..., "description": ..., "directories": [...] } ] } ] }

ZONE LABELLING GUIDANCE — assign by what the directory actually contains:
- presentation/routing: HTTP routers, endpoints, controllers, CLI entry points, UI components
- business/domain: service classes, orchestration, processing, matching, domain logic
- data: repositories, ORM/domain models, dataclasses, persistence, schemas
- config: settings, dependency wiring, app bootstrap (main.py, dependencies.py, core/)
- tools: tool/adapter wrappers, integrations
```

### G.3 Flow namer — `agents/tracer_agent/prompts/flow_name_prompt.py` (`PROMPT_VERSION = "2"`)

Worth quoting one passage for the dissertation, because it shows the project actively resisting the
failure mode its own thesis identifies — naming nodes after code symbols rather than after what they
do:

```
- steps: verb phrases for what the step DOES ("Fetch & persist sources", "Parse & validate request").
- decisions: the QUESTION being decided ("What kind of request?").
- arms: the ANSWER that the arm represents.
- effects: a NOUN for the side effect and its target ("Neon: repo_map", "Anthropic: messages").
- Never a class, function, or file name unless nothing better exists — this includes a humanized
  version of one with spaces inserted. "Branch Detector" and "Ticket View Set" are still class
  names wearing spaces and are NOT acceptable; say what they DO instead, e.g. "Detect code
  branches", "Serve ticket API requests".
```

### G.4 Remaining prompts

| Prompt | File | Lines |
|---|---|---|
| Flow reviewer | `agents/tracer_agent/prompts/flow_review_prompt.py` | 87 |
| Stitch judge | `agents/tracer_agent/prompts/stitch_judge_prompt.py` | 52 |
| Flow label (layout agent) | `agents/layout_agent/prompts/flow_label_prompt.py` | 93 |
| Symbol explain | `agents/explain_agent/prompts/explain_prompt.py` | 71 |

**No correction/critic prompt exists in the current system.** `CorrectionPromptBuilder` was deleted
at `774102a`; its text is recovered and analysed in `02_decision_algorithm.md` §2.1.

---

## Appendix H — Work-package record

The project used two overlapping planning systems. Both are in the repository.

### H.1 `features/` — the decision-flow tracer specification (13 features)

Authored 15 July 2026 at `dd9b953`, implemented 15–16 July in thirteen consecutive commits. This is
the specification for the central pivot.

| ID | Title | Implementing commit |
|---|---|---|
| F01 | FlowGraph shared models | `c3a01aa` |
| F02 | Project indexer | `8897cc0` |
| F03 | Call resolver | `87fd00d` |
| F04 | Dispatch-site extraction | `12e4ef7` |
| F05 | Effect detection | `0af6297` |
| F06 | Significance filter & ranking | `5874f20` |
| F07 | Flow condensation (FlowGraph construction) | `35506ed` |
| F08 | Cross-service stitching | `3cb173f` |
| F09 | One-page budget | `66a0ab1` |
| F10 | Flow labeling (the only LLM stage) | `5ee73a7` |
| F11 | Flow layout (geometry) | `2d09ea1` |
| F12 | Frontend: the one-page view | `8453760` |
| F13 | Pipeline cutover & deletion | `774102a` |

**One-to-one traceability from specification to commit** — the strongest single piece of LO1
evidence in the project.

### H.2 `pbis/` — the PBI backlog (33 present, 1–33 removed)

`CLAUDE.md` states PBIs are ephemeral: *"gitignored and removed on merge to main."* PBIs 1–33 are
therefore **not recoverable**; `pbis/README.md` documents Phase 1 (PBIs 1–6) retrospectively.

| PBI | Title |
|---|---|
| 34 | Capture component source line ranges (tracer) |
| 35 | Neon code store + source persistence (tracer) |
| 36 | Code-serving endpoint (api gateway) |
| 37 | Frontend: code-view toggle + code panel |
| 38 | Neon diagram-edit store (shared) |
| 39 | Diagram-edits endpoint (api gateway) |
| 40 | Frontend: diagram-edits API helper + proxy |
| 41 | Frontend: overlay merge helper |
| 42 | Frontend: diagram-edit state hook |
| 43 | Frontend: editable text-box node |
| 44 | Frontend: edit toolbar ribbon |
| 45 | Frontend: FlowGraph edit-mode wiring |
| 46 | Frontend: inline label editing on existing nodes |
| 47 | Frontend: wire edit mode through the page |
| 48 | Progress bar survives page close/reopen |
| 49 | Dashboard: "Select GitHub Repo" button + picker |
| 50 | Persist GitHub token server-side + list current user's repos |
| 51 | Background GitHub analysis with progress |
| 52 | Frontend: GitHub picker via stored token + unified progress |
| 53 | Light/dark theme infrastructure + Settings toggle + chrome light mode |
| 54 | Light mode for the diagram canvas, nodes, edges & panels |
| 55 | Cache the repo-maps list across navigation |
| 56 | Emit the full graph with visibility levels (stop deleting decisions) |
| 57 | Carry containment metadata (`owner_fqn`, `arm_path`, `containers`) |
| 58 | Derive `hidden_children` from containment, not graph adjacency |
| 59 | Terminal outcome nodes (every decision leads somewhere) |
| 60 | Linear runs render as a pipeline; siblings stop overlapping |
| 61 | Sequential decisions form one chain; pipelines render rigidly |
| 62 | Refactor: delete dead code, remove triplication, refresh the docs |
| 63 | `FlowNamer`: cached, batched LLM naming inside the tracer |
| 64 | `FlowReviewer`: sibling-aware coherence pass, and retire duplicate labelling |
| 65 | The full card: label + summary + provenance on every node face |
| 66 | Unreachable islands crash the pipeline; establish I2 instead of only asserting it |

PBIs 56–61 are the progressive-disclosure work package; 63–66 are the labelling and robustness pass.

**No sprint or Kanban record exists in the repository.** There are no GitHub Projects boards, issue
templates or milestone files. The planning record is `features/`, `pbis/`, `CLAUDE.md`, `PROMPT.md`
and `HANDOFF.md`.

### H.3 The development process itself (LO1 evidence)

`CLAUDE.md` and `PROMPT.md` document a three-role workflow that is unusual enough to be worth
describing in the dissertation:

> 1. **Opus plans** — breaks work into small, self-contained scoped task docs ("PBIs").
> 2. **Sonnet implements** — Opus spawns a Sonnet sub-agent per scoped task.
> 3. **Opus reviews** — reviews the diff against that task's acceptance before accepting it.

Alongside it, `CLAUDE.md` codifies eleven engineering rules, several written in direct response to
specific incidents and quoting the damage each caused — for example "Never Read Configuration From
The Ambient Environment" (which had "already shipped a fully degraded product": 22 nodes where the
scripts produced 394, silently) and "Never Hardcode This Repo's Own Layout" (which "cost two separate
outages of the whole feature"). Documented post-incident rule-making is good LO1 material.

---

## Gaps and open questions

1. **PBIs 1–33 are unrecoverable.** Gitignored and deleted by design. `pbis/README.md` describes
   PBIs 1–6 retrospectively; 7–33 have no surviving record beyond commit messages and PR titles.
   If the dissertation needs a complete backlog, PR bodies on GitHub (`gh pr view <n>`) are the only
   remaining source.
2. **No sprint, Kanban or time record exists.** LO1 asks about planning and control; the evidence
   available is specification-to-commit traceability (H.1) and the rule set, not a schedule or
   velocity record. If planning artefacts exist outside the repository, they should be cited.
3. **`features/` covers only the July pivot.** The April–June work (profiler, layout agent, templates,
   code view) has no equivalent specification set — those were PBIs, now deleted.
4. **Prompt version history is not tracked.** `PROMPT_VERSION` is `"2"` for the decision judge and
   flow namer; version `"1"` is not preserved anywhere, so prompt evolution cannot be shown.
