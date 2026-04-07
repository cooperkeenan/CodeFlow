from pydantic import BaseModel


class ProfileRequest(BaseModel):
    access_token: str
    repo_name: str


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