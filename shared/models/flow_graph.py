from typing import Literal

from pydantic import BaseModel, model_validator

NodeKind = Literal["entry", "step", "decision", "parallel", "effect"]
EdgeKind = Literal["sequence", "arm", "parallel", "stitch"]
Confidence = Literal["resolved", "inferred", "dynamic"]
EffectKind = Literal["http_out", "database", "llm", "file", "queue", "email", "response"]
Badge = Literal["loop", "recursive", "dynamic", "guarded", "folded"]


class SourceRef(BaseModel):
    file: str
    line: int
    end_line: int


class FlowNode(BaseModel):
    id: str
    kind: NodeKind
    lane: str
    label: str
    llm_label: str | None = None
    one_liner: str = ""
    backing: list[str] = []
    refs: list[SourceRef] = []
    badges: list[Badge] = []
    folded_count: int = 0
    effect_kind: EffectKind | None = None
    effect_target: str = ""


class FlowEdge(BaseModel):
    source: str
    target: str
    kind: EdgeKind
    arm_label: str = ""
    llm_label: str | None = None
    group_id: str = ""
    confidence: Confidence = "resolved"
    is_spine: bool = False


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
        self.edges.sort(key=lambda edge: (edge.source, edge.target, edge.arm_label))
        return self
