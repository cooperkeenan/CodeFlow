from typing import Literal

from pydantic import BaseModel

from shared.models.diagram_spec import ComponentTier, EdgeType

DiagramType = Literal[
    "pipeline", "hub_and_spoke", "layered_tier", "hierarchy",
    "mesh", "dependency_graph", "relationship",
]


class TemplateNode(BaseModel):
    id: str
    label: str
    tier: ComponentTier
    module_name: str
    kind: Literal["module", "component", "zone", "cluster"] = "module"
    parent: str | None = None
    style: str | None = None
    zone_count: int = 0
    component_count: int = 0
    drillable: bool = False


class TemplateEdge(BaseModel):
    source: str
    target: str
    edge_type: EdgeType


class DiagramTemplate(BaseModel):
    type: DiagramType
    nodes: list[TemplateNode]
    edges: list[TemplateEdge]
    meta: dict = {}


class RenderedView(BaseModel):
    type: str
    nodes: list[dict]
    edges: list[dict]
