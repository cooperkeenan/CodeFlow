from fastapi import APIRouter, Depends
from gateway.deps import get_password_auth_service
from gateway.models.auth_model import LoginRequest, SignInResponse, SignupRequest
from gateway.services.password_auth_service import PasswordAuthService

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/signup", response_model=SignInResponse)
async def signup(
    request: SignupRequest,
    service: PasswordAuthService = Depends(get_password_auth_service),
) -> SignInResponse:
    return await service.register(request.email, request.password)


@router.post("/login", response_model=SignInResponse)
async def login(
    request: LoginRequest,
    service: PasswordAuthService = Depends(get_password_auth_service),
) -> SignInResponse:
    return await service.login(request.email, request.password)
