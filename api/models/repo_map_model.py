from datetime import datetime

from pydantic import BaseModel

from models.analysis_model import AnalyseResponse


class RepoMapSummary(BaseModel):
    repo: str
    source: str
    created_at: datetime | None
    updated_at: datetime | None


class RepoMapListResponse(BaseModel):
    repo_maps: list[RepoMapSummary]


class RepoMapDetail(BaseModel):
    repo: str
    source: str
    created_at: datetime | None
    updated_at: datetime | None
    map: AnalyseResponse
