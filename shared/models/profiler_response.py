from pydantic import BaseModel

from shared.models.layer_hints import LayerHints


class ProfileResponse(BaseModel):
    architecture_type: str
    language: str
    framework: str
    patterns: list[str]
    entry_point_hint: str
    layer_hints: LayerHints