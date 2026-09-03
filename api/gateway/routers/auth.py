from fastapi import APIRouter, Depends, Response
from gateway.deps import get_password_auth_service, get_password_reset_service
from gateway.models.auth_model import (
    ForgotPasswordRequest,
    LoginRequest,
    ResetPasswordRequest,
    SignInResponse,
    SignupRequest,
)
from gateway.services.password_auth_service import PasswordAuthService
from gateway.services.password_reset_service import PasswordResetService

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


@router.post("/forgot-password", status_code=204)
async def forgot_password(
    request: ForgotPasswordRequest,
    service: PasswordResetService = Depends(get_password_reset_service),
) -> Response:
    await service.request_reset(request.email)
    return Response(status_code=204)


@router.post("/reset-password", status_code=204)
async def reset_password(
    request: ResetPasswordRequest,
    service: PasswordResetService = Depends(get_password_reset_service),
) -> Response:
    await service.reset(request.token, request.password)
    return Response(status_code=204)
