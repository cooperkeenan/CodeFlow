from typing import Literal

from pydantic import BaseModel

EdgeType = Literal["http", "import", "database", "event", "call", "sequence"]


class ComponentIO(BaseModel):
    inputs: list[str] = []
    outputs: list[str] = []


ComponentTier = Literal["primary", "secondary"]


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


LayoutStyle = Literal["grid", "stack", "pipeline", "hierarchy", "hub"]


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


Archetype = Literal["pipeline", "hub", "layered", "hierarchy", "mesh"]


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


Cluster.model_rebuild()