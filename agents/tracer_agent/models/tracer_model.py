from pydantic import BaseModel

from shared.models.diagram_spec import DiagramSpec


class TracerResponse(BaseModel):
    architecture_type: str
    diagram_spec: DiagramSpec