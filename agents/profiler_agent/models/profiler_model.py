from pydantic import BaseModel


class ProfileRequest(BaseModel):
    repo_name: str
    access_token: str | None = None
    local_path: str | None = None


class LayerHints(BaseModel):
    presentation: list[str] = []
    business: list[str] = []
    data: list[str] = []


class ProfileResponse(BaseModel):
    architecture_type: str
    language: str
    framework: str
    patterns: list[str]
    entry_point_hint: str
    layer_hints: LayerHints