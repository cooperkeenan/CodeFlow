from pydantic import BaseModel

from shared.models.flow_graph import FlowGraph


class LayoutRequest(BaseModel):
    flow_graph: FlowGraph


class LayoutResponse(BaseModel):
    flow_graph: FlowGraph
