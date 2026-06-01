from pydantic import BaseModel

from shared.models.repo_blueprint import RepoBlueprint


class TracerRequest(BaseModel):
    access_token: str | None = None
    repo_name: str
    local_path: str | None = None
    architecture_type: str
    language: str
    entry_point_hint: str = ""
    blueprint: RepoBlueprint
