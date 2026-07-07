from datetime import datetime

from pydantic import BaseModel


class CreateTokenRequest(BaseModel):
    name: str


class CreatedToken(BaseModel):
    id: int
    name: str | None
    token: str
    prefix: str
    created_at: datetime | None = None


class TokenSummary(BaseModel):
    id: int
    name: str | None
    prefix: str
    created_at: datetime | None
    last_used_at: datetime | None
    revoked_at: datetime | None
