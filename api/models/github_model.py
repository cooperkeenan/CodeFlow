from pydantic import BaseModel


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