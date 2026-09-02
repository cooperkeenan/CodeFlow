from datetime import datetime

from pydantic import BaseModel

from shared.models.profiler_response import ProfileResponse


class AnalyseRequest(BaseModel):
    access_token: str | None = None
    repo_name: str
    local_path: str | None = None
    archive_gz: str | None = None


class AnalyseResponse(BaseModel):
    repo: str
    profile: ProfileResponse
    trace: dict
    diagram: dict = {}


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


class NodeExplainRequest(BaseModel):
    node_id: str


class DiagramEditsResponse(BaseModel):
    repo: str
    edits: dict


class DiagramEditsPutRequest(BaseModel):
    edits: dict
