from datetime import datetime

from pydantic import BaseModel


class AuthUser(BaseModel):
    id: int
    github_id: int | None = None
    github_login: str | None = None
    email: str | None = None


class SignInResponse(BaseModel):
    session_token: str
    github_access_token: str = ""
    user: AuthUser


class SignupRequest(BaseModel):
    email: str
    password: str


class LoginRequest(BaseModel):
    email: str
    password: str


class ForgotPasswordRequest(BaseModel):
    email: str


class ResetPasswordRequest(BaseModel):
    token: str
    password: str


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


class GitHubCallbackRequest(BaseModel):
    code: str


class GitHubCallbackResponse(BaseModel):
    access_token: str


class RepositoryResponse(BaseModel):
    name: str
    full_name: str
    owner: str
    description: str | None
    url: str
    language: str | None


class RepositoriesResponse(BaseModel):
    repositories: list[RepositoryResponse]
