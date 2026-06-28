from fastapi import APIRouter, Depends

from dependencies import get_placement_service
from models.render_model import RenderRequest, RenderResponse
from services.placement_service import PlacementService

router = APIRouter(tags=["render"])


@router.post("/render", response_model=RenderResponse)
async def render(
    request: RenderRequest,
    service: PlacementService = Depends(get_placement_service),
) -> RenderResponse:
    views = service.render(request.diagram_templates)
    return RenderResponse(views=views)
