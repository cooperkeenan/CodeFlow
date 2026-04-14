from pydantic import BaseModel

from shared.models.diagram_spec import DiagramSpec


class RenderRequest(BaseModel):
    architecture_type: str
    diagram_spec: DiagramSpec


class RenderResponse(BaseModel):
    mermaid: str