from pydantic import BaseModel

from shared.models.flow_graph import FlowGraph
from shared.models.rendered_view import RenderedView


class RenderRequest(BaseModel):
    flow_graph: FlowGraph
    lane_headers: bool = True


class RenderResponse(BaseModel):
    view: RenderedView
