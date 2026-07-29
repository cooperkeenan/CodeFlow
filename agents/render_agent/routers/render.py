from fastapi import APIRouter, Depends

from dependencies import get_flow_page_placer
from models.render_model import RenderRequest, RenderResponse
from placement.flow_page_placer import FlowPagePlacer

router = APIRouter(tags=["render"])


@router.post("/render", response_model=RenderResponse)
async def render(
    request: RenderRequest,
    placer: FlowPagePlacer = Depends(get_flow_page_placer),
) -> RenderResponse:
    view = placer.place(request.flow_graph)
    return RenderResponse(view=view)
