# F01 — FlowGraph shared models

Depends on: —
Deliverable: `shared/models/flow_graph.py` (+ split files if >150 lines)

## Why

Every downstream feature (tracer stages, labeling, layout, frontend) consumes or
produces this contract. It replaces `DiagramSpec`/`DiagramTemplate` as the primary
diagram payload. Ship it first so 11/12 can build against it in parallel.

## Spec

Pydantic v2 models. All ids are **stable content-derived strings**, never uuids, so
re-runs and frontend diffs are stable.

```python
NodeKind = Literal["entry", "step", "decision", "parallel", "effect"]
EdgeKind = Literal["sequence", "arm", "parallel", "stitch"]
Confidence = Literal["resolved", "inferred", "dynamic"]
EffectKind = Literal["http_out", "database", "llm", "file", "queue", "email", "response"]
Badge = Literal["loop", "recursive", "dynamic", "guarded", "folded"]

class SourceRef(BaseModel):
    file: str          # repo-relative path
    line: int
    end_line: int

class FlowNode(BaseModel):
    id: str            # entry:<fqn> | step:<first_fqn>:<line> | dec:<fqn>:<line> | par:<fqn>:<line> | eff:<fqn>:<line>
    kind: NodeKind
    lane: str
    label: str         # deterministic source-derived fallback (always present)
    llm_label: str | None = None
    one_liner: str = ""
    backing: list[str] = []        # ordered component/function fqns condensed into this node
    refs: list[SourceRef] = []
    badges: list[Badge] = []
    folded_count: int = 0          # >0 when arms/steps were folded under budget
    effect_kind: EffectKind | None = None   # only for kind="effect"
    effect_target: str = ""                  # url path / table / model id hint

class FlowEdge(BaseModel):
    source: str
    target: str
    kind: EdgeKind
    arm_label: str = ""            # source-derived ("== 'cat'", "POST /trace", "ValueError")
    llm_label: str | None = None
    group_id: str = ""             # dispatch-site id shared by sibling arms (XOR group)
    confidence: Confidence = "resolved"
    is_spine: bool = False         # set by layout: the bold happy path

class Lane(BaseModel):
    id: str
    name: str
    llm_title: str | None = None
    entry_ids: list[str]
    mass: float                    # significance mass, used for budget + ordering

class FlowGraph(BaseModel):
    repo: str
    page_title: str = ""
    lanes: list[Lane]
    nodes: list[FlowNode]
    edges: list[FlowEdge]
    meta: dict = {}                # budget used, counts, version
```

Rules:
- Sibling arms of one decision share `group_id` and are mutually exclusive (XOR).
  Edges out of a `parallel` node use kind `parallel` (AND). `stitch` edges connect an
  `http_out` effect to an `entry` in another lane.
- `label` must always be renderable without the LLM (see F10 fallbacks).
- Lists are sorted (`nodes` by id, `edges` by (source, target, arm_label)) at
  construction time so serialized output is canonical.

## Non-goals

Tracer-internal records (DispatchSite, CallSite, ProjectIndex) are NOT shared models;
they live in `agents/tracer_agent/models/` (F02–F06).

## Acceptance

- Round-trip: `FlowGraph.model_validate(g.model_dump())` is identity.
- Two constructions with the same content in different insertion orders serialize
  byte-identically.
