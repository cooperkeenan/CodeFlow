from pydantic import BaseModel

from shared.models.diagram_template import RenderedView
from shared.models.flow_graph import FlowGraph


class RenderRequest(BaseModel):
    flow_graph: FlowGraph


class RenderResponse(BaseModel):
    view: RenderedView
