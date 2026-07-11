from fastapi import HTTPException

from models.auth_model import AuthUser, SignInResponse
from services.password_hasher import PasswordHasher
from services.token_hasher import TokenHasher

from shared.access_token_store.access_token_store import AccessTokenStore
from shared.user_store.user_store import UserStore

_SESSION_KIND = "session"
_SESSION_PREFIX = "cfs_"


class PasswordAuthService:
    def __init__(
        self,
        user_store: UserStore,
        token_store: AccessTokenStore,
        hasher: TokenHasher,
        password_hasher: PasswordHasher,
    ) -> None:
        self._users = user_store
        self._tokens = token_store
        self._hasher = hasher
        self._passwords = password_hasher

    async def register(self, email: str, password: str) -> SignInResponse:
        if await self._users.get_by_email(email) is not None:
            raise HTTPException(status_code=409, detail="Email already registered")
        password_hash = self._passwords.hash(password)
        user_id = await self._users.create_with_password(email, password_hash)
        return await self._issue(user_id, email)

    async def login(self, email: str, password: str) -> SignInResponse:
        record = await self._users.get_by_email(email)
        if record is None or record["password_hash"] is None:
            raise HTTPException(status_code=401, detail="Invalid email or password")
        if not self._passwords.verify(password, record["password_hash"]):
            raise HTTPException(status_code=401, detail="Invalid email or password")
        return await self._issue(record["id"], email)

    async def _issue(self, user_id: int, email: str) -> SignInResponse:
        raw, token_hash, prefix = self._hasher.mint(_SESSION_PREFIX)
        await self._tokens.create(user_id, _SESSION_KIND, None, token_hash, prefix)
        user = AuthUser(id=user_id, email=email)
        return SignInResponse(session_token=raw, user=user)
