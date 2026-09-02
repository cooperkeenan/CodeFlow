from pydantic import BaseModel

from shared.models.flow_graph import FlowGraph


class TracerResponse(BaseModel):
    flow_graph: FlowGraph
