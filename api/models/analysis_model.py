from pydantic import BaseModel

from shared.models.profiler_response import ProfileResponse
from shared.models.tracer_request import TracerRequest


class AnalyseRequest(BaseModel):
    access_token: str | None = None
    repo_name: str
    local_path: str | None = None


class AnalyseResponse(BaseModel):
    repo: str
    profile: ProfileResponse
    trace: dict
    mermaid: str