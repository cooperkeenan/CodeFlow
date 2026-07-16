from fastapi import APIRouter, Depends

from dependencies import get_flow_labeler
from models.layout_model import LayoutRequest, LayoutResponse
from services.planning.flow_labeler import FlowLabeler

router = APIRouter(tags=["layout"])


@router.post("/layout", response_model=LayoutResponse)
async def layout(
    request: LayoutRequest,
    labeler: FlowLabeler = Depends(get_flow_labeler),
) -> LayoutResponse:
    labeled = await labeler.label(request.flow_graph)
    return LayoutResponse(flow_graph=labeled)
