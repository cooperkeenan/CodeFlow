from typing import Literal

from pydantic import BaseModel

EdgeType = Literal["http", "import", "database", "event", "call"]


class Component(BaseModel):
    name: str
    description: str
    file_path: str


class Edge(BaseModel):
    source: str
    target: str
    edge_type: EdgeType


class DiagramSpec(BaseModel):
    architecture_type: str
    layers: dict[str, list[Component]]
    edges: list[Edge]