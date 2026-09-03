import logging
from datetime import datetime, timedelta, timezone

from fastapi import HTTPException
from gateway.services.email_sender import EmailSender
from gateway.services.password_hasher import PasswordHasher
from gateway.services.token_hasher import TokenHasher

from shared.access_token_store.access_token_store import AccessTokenStore
from shared.user_store.user_store import UserStore

logger = logging.getLogger(__name__)

_RESET_KIND = "password_reset"
_RESET_PREFIX = "cfr_"
_SESSION_KIND = "session"
_TTL = timedelta(hours=1)
_MIN_PASSWORD_LENGTH = 8
_SUBJECT = "Reset your CodeFlow password"
_BODY = (
    "We received a request to reset your CodeFlow password.\n\n"
    "Open this link to choose a new one:\n{link}\n\n"
    "The link expires in 1 hour and can only be used once.\n"
    "If you did not request this, you can ignore this email."
)


class PasswordResetService:
    def __init__(
        self,
        user_store: UserStore,
        token_store: AccessTokenStore,
        hasher: TokenHasher,
        password_hasher: PasswordHasher,
        email_sender: EmailSender,
        app_base_url: str,
    ) -> None:
        self._users = user_store
        self._tokens = token_store
        self._hasher = hasher
        self._passwords = password_hasher
        self._email = email_sender
        self._base_url = app_base_url.rstrip("/")

    async def request_reset(self, email: str) -> None:
        record = await self._users.get_by_email(email)
        if record is None or record["password_hash"] is None:
            logger.info("password reset requested for unknown address")
            return
        raw, token_hash, prefix = self._hasher.mint(_RESET_PREFIX)
        await self._tokens.create(record["id"], _RESET_KIND, None, token_hash, prefix)
        link = f"{self._base_url}/reset-password?token={raw}"
        await self._email.send(email, _SUBJECT, _BODY.format(link=link))

    async def reset(self, raw_token: str, new_password: str) -> None:
        if len(new_password) < _MIN_PASSWORD_LENGTH:
            raise HTTPException(
                status_code=400,
                detail=f"Password must be at least {_MIN_PASSWORD_LENGTH} characters",
            )
        record = await self._tokens.get_by_hash(self._hasher.hash(raw_token))
        if record is None or record["kind"] != _RESET_KIND:
            raise HTTPException(status_code=400, detail="Invalid or expired reset link")
        if record["revoked_at"] is not None or self._expired(record["created_at"]):
            raise HTTPException(status_code=400, detail="Invalid or expired reset link")
        await self._users.set_password(record["user_id"], self._passwords.hash(new_password))
        await self._tokens.revoke(record["user_id"], record["id"])
        await self._tokens.revoke_kind(record["user_id"], _SESSION_KIND)

    def _expired(self, created_at: datetime | None) -> bool:
        if created_at is None:
            return True
        return datetime.now(timezone.utc) - created_at > _TTL
