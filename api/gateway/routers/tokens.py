from fastapi import APIRouter, Depends, HTTPException, Response
from gateway.deps import get_current_user, get_token_service
from gateway.models.auth_model import (
    AuthUser,
    CreatedToken,
    CreateTokenRequest,
    TokenSummary,
)
from gateway.services.token_service import TokenService

router = APIRouter(prefix="/tokens", tags=["tokens"])


@router.post("", response_model=CreatedToken)
async def create_token(
    request: CreateTokenRequest,
    user: AuthUser = Depends(get_current_user),
    service: TokenService = Depends(get_token_service),
) -> CreatedToken:
    return await service.create(user.id, request.name)


@router.get("", response_model=list[TokenSummary])
async def list_tokens(
    user: AuthUser = Depends(get_current_user),
    service: TokenService = Depends(get_token_service),
) -> list[TokenSummary]:
    return await service.list(user.id)


@router.delete("/{token_id}", status_code=204)
async def revoke_token(
    token_id: int,
    user: AuthUser = Depends(get_current_user),
    service: TokenService = Depends(get_token_service),
) -> Response:
    revoked = await service.revoke(user.id, token_id)
    if not revoked:
        raise HTTPException(status_code=404, detail="Token not found")
    return Response(status_code=204)
