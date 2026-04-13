from pydantic import BaseModel

from shared.models.profiler_response import ProfileResponse
from agents.tracer_agent.models.tracer_model import TracerResponse


class AnalyseRequest(BaseModel):
    access_token: str | None = None
    repo_name: str
    local_path: str | None = None


class AnalyseResponse(BaseModel):
    repo: str
    profile: ProfileResponse
    trace: TracerResponse
