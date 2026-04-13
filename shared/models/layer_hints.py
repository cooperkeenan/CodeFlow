from pydantic import BaseModel


class LayerHints(BaseModel):
    presentation: list[str] = []
    business: list[str] = []
    data: list[str] = []