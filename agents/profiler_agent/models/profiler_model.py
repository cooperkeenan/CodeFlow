from pydantic import BaseModel

from shared.models.layer_hints import LayerHints 
from shared.models.profiler_response import ProfileResponse


class ProfileRequest(BaseModel):
    repo_name: str
    access_token: str | None = None
    local_path: str | None = None
