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
