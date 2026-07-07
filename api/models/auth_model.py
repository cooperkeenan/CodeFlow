from pydantic import BaseModel


class AuthUser(BaseModel):
    id: int
    github_id: int
    github_login: str


class SignInResponse(BaseModel):
    session_token: str
    github_access_token: str
    user: AuthUser
