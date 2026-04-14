from fastapi import APIRouter, Depends

from dependencies import get_mermaid_service
from models.render_model import RenderRequest, RenderResponse
from services.mermaid_service import MermaidService

router = APIRouter(tags=["render"])


@router.post("/render", response_model=RenderResponse)
async def render(
    request: RenderRequest,
    service: MermaidService = Depends(get_mermaid_service),
) -> RenderResponse:
    mermaid = service.render(request.diagram_spec)
    return RenderResponse(mermaid=mermaid)