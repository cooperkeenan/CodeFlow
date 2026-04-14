from typing import Literal

from pydantic import BaseModel

EdgeType = Literal["http", "import", "database", "event", "call"]


class ComponentIO(BaseModel):
    inputs: list[str] = []
    outputs: list[str] = []


class Component(BaseModel):
    name: str
    description: str
    file_path: str
    io: ComponentIO | None = None
    children: list[str] = []


class Edge(BaseModel):
    source: str
    target: str
    edge_type: EdgeType


class ExternalActor(BaseModel):
    name: str
    type: Literal["database", "api", "webhook", "browser"]
    description: str


class DiagramSpec(BaseModel):
    architecture_type: str
    layers: dict[str, list[Component]]
    edges: list[Edge]
    external_actors: list[ExternalActor] = []
    entry_points: list[str] = []