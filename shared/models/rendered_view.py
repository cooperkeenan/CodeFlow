from pydantic import BaseModel


class RenderedView(BaseModel):
    type: str
    page_title: str = ""
    nodes: list[dict]
    edges: list[dict]
    hidden: list[dict] = []
    hidden_edges: list[dict] = []
    node_geometry: dict[str, dict[str, int]] = {}
