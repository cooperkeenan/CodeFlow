import logging

from gateway.models.auth_model import AuthUser, SignInResponse
from gateway.services.github_service import GitHubService
from gateway.services.token_hasher import TokenHasher

from shared.access_token_store.access_token_store import AccessTokenStore
from shared.user_store.user_store import UserStore

logger = logging.getLogger(__name__)

_SESSION_KIND = "session"
_SESSION_PREFIX = "cfs_"
_LOGIN_KINDS = frozenset({"session", "api"})


class AuthService:
    def __init__(
        self,
        user_store: UserStore,
        token_store: AccessTokenStore,
        github_service: GitHubService,
        hasher: TokenHasher,
    ) -> None:
        self._users = user_store
        self._tokens = token_store
        self._github = github_service
        self._hasher = hasher

    async def sign_in(self, code: str) -> SignInResponse:
        github_token = await self._github.exchange_code_for_token(code)
        identity = await self._github.get_identity(github_token)
        user_id = await self._users.upsert(
            identity["id"], identity["login"], identity["name"], identity["avatar_url"]
        )
        await self._users.set_github_token(user_id, github_token)
        raw, token_hash, prefix = self._hasher.mint(_SESSION_PREFIX)
        await self._tokens.create(user_id, _SESSION_KIND, None, token_hash, prefix)
        user = AuthUser(id=user_id, github_id=identity["id"], github_login=identity["login"])
        return SignInResponse(session_token=raw, github_access_token=github_token, user=user)

    async def link_github(self, user: AuthUser, code: str) -> AuthUser:
        github_token = await self._github.exchange_code_for_token(code)
        identity = await self._github.get_identity(github_token)
        await self._users.link_github(
            user.id,
            identity["id"],
            identity["login"],
            identity["name"],
            identity["avatar_url"],
        )
        await self._users.set_github_token(user.id, github_token)
        record = await self._users.get(user.id)
        if record is None:
            raise ValueError(f"User {user.id} not found after upsert")
        return AuthUser(
            id=record["id"],
            github_id=record["github_id"],
            github_login=record["github_login"],
            email=record["email"],
        )

    async def resolve(self, raw_token: str) -> AuthUser | None:
        record = await self._tokens.get_by_hash(self._hasher.hash(raw_token))
        if record is None or record["revoked_at"] is not None:
            return None
        if record["kind"] not in _LOGIN_KINDS:
            return None
        user = await self._users.get(record["user_id"])
        if user is None:
            return None
        await self._tokens.touch_last_used(record["id"])
        return AuthUser(
            id=user["id"],
            github_id=user["github_id"],
            github_login=user["github_login"],
            email=user["email"],
        )
