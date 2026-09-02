from fastapi import APIRouter, Depends
from gateway.deps import get_current_user, get_diagram_edit_service
from gateway.models.auth_model import AuthUser
from gateway.models.repo_map_model import (
    DiagramEditsPutRequest,
    DiagramEditsResponse,
)
from gateway.services.diagram_edit_service import DiagramEditService

router = APIRouter(tags=["diagram-edits"])


@router.get("/diagram/edits", response_model=DiagramEditsResponse)
async def get_diagram_edits(
    repo: str,
    user: AuthUser = Depends(get_current_user),
    service: DiagramEditService = Depends(get_diagram_edit_service),
) -> DiagramEditsResponse:
    edits = await service.get(user.id, repo)
    return DiagramEditsResponse(repo=repo, edits=edits)


@router.put("/diagram/edits", response_model=DiagramEditsResponse)
async def put_diagram_edits(
    repo: str,
    body: DiagramEditsPutRequest,
    user: AuthUser = Depends(get_current_user),
    service: DiagramEditService = Depends(get_diagram_edit_service),
) -> DiagramEditsResponse:
    await service.save(user.id, repo, body.edits)
    return DiagramEditsResponse(repo=repo, edits=body.edits)
