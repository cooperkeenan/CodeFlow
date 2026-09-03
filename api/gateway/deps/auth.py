from fastapi import Depends, Header, HTTPException

from gateway.core.config import get_settings
from gateway.deps.clients import get_github_service
from gateway.deps.stores import get_token_store, get_user_store
from gateway.models.auth_model import AuthUser
from gateway.services.auth_service import AuthService
from gateway.services.email_sender import (
    EmailSender,
    LoggingEmailSender,
    SmtpEmailSender,
)
from gateway.services.password_reset_service import PasswordResetService
from gateway.services.github_service import GitHubService
from gateway.services.password_auth_service import PasswordAuthService
from gateway.services.password_hasher import PasswordHasher
from gateway.services.token_hasher import TokenHasher
from shared.access_token_store.access_token_store import AccessTokenStore
from shared.user_store.user_store import UserStore


def get_token_hasher() -> TokenHasher:
    return TokenHasher()


def get_auth_service(
    user_store: UserStore = Depends(get_user_store),
    token_store: AccessTokenStore = Depends(get_token_store),
    github_service: GitHubService = Depends(get_github_service),
    hasher: TokenHasher = Depends(get_token_hasher),
) -> AuthService:
    return AuthService(user_store, token_store, github_service, hasher)


def get_password_hasher() -> PasswordHasher:
    return PasswordHasher()


def get_password_auth_service(
    user_store: UserStore = Depends(get_user_store),
    token_store: AccessTokenStore = Depends(get_token_store),
    hasher: TokenHasher = Depends(get_token_hasher),
    password_hasher: PasswordHasher = Depends(get_password_hasher),
) -> PasswordAuthService:
    return PasswordAuthService(user_store, token_store, hasher, password_hasher)


def get_email_sender() -> EmailSender:
    settings = get_settings()
    if not settings.SMTP_HOST:
        return LoggingEmailSender()
    return SmtpEmailSender(
        settings.SMTP_HOST,
        settings.SMTP_PORT,
        settings.SMTP_USER,
        settings.SMTP_PASSWORD,
        settings.SMTP_FROM,
    )


def get_password_reset_service(
    user_store: UserStore = Depends(get_user_store),
    token_store: AccessTokenStore = Depends(get_token_store),
    hasher: TokenHasher = Depends(get_token_hasher),
    password_hasher: PasswordHasher = Depends(get_password_hasher),
    email_sender: EmailSender = Depends(get_email_sender),
) -> PasswordResetService:
    return PasswordResetService(
        user_store,
        token_store,
        hasher,
        password_hasher,
        email_sender,
        get_settings().APP_BASE_URL,
    )


def _bearer_token(authorization: str | None) -> str | None:
    if not authorization or not authorization.lower().startswith("bearer "):
        return None
    return authorization[7:].strip()


async def get_current_user(
    authorization: str | None = Header(default=None),
    auth: AuthService = Depends(get_auth_service),
) -> AuthUser:
    raw = _bearer_token(authorization)
    user = await auth.resolve(raw) if raw else None
    if user is None:
        raise HTTPException(status_code=401, detail="Invalid or missing token")
    return user


async def get_optional_user(
    authorization: str | None = Header(default=None),
    auth: AuthService = Depends(get_auth_service),
) -> AuthUser | None:
    raw = _bearer_token(authorization)
    if not raw:
        return None
    return await auth.resolve(raw)
