from pydantic import BaseModel


class AnalyseRequest(BaseModel):
    access_token: str
    repo_name: str


class AnalyseResponse(BaseModel):
    repo: str
    profile: dict