from gateway.models.auth_model import CreatedToken, TokenSummary
from gateway.services.token_hasher import TokenHasher

from shared.access_token_store.access_token_store import AccessTokenStore

_API_KIND = "api"
_API_PREFIX = "cf_"


class TokenService:
    def __init__(self, token_store: AccessTokenStore, hasher: TokenHasher) -> None:
        self._tokens = token_store
        self._hasher = hasher

    async def create(self, user_id: int, name: str) -> CreatedToken:
        raw, token_hash, prefix = self._hasher.mint(_API_PREFIX)
        token_id = await self._tokens.create(user_id, _API_KIND, name, token_hash, prefix)
        return CreatedToken(id=token_id, name=name, token=raw, prefix=prefix)

    async def list(self, user_id: int) -> list[TokenSummary]:
        rows = await self._tokens.list_for_user(user_id, _API_KIND)
        return [
            TokenSummary(
                id=r["id"],
                name=r["name"],
                prefix=r["token_prefix"],
                created_at=r["created_at"],
                last_used_at=r["last_used_at"],
                revoked_at=r["revoked_at"],
            )
            for r in rows
        ]

    async def revoke(self, user_id: int, token_id: int) -> bool:
        return await self._tokens.revoke(user_id, token_id)
