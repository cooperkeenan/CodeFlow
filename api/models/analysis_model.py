from pydantic import BaseModel


class AnalyseRequest(BaseModel):
    access_token: str | None = None
    repo_name: str
    local_path: str | None = None


class AnalyseResponse(BaseModel):
    repo: str
    profile: dict