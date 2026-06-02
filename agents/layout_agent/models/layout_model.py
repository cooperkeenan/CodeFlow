from pydantic import BaseModel

from shared.models.diagram_spec import DiagramSpec, LayoutHint


class LayoutRequest(BaseModel):
    diagram_spec: DiagramSpec


class LayoutResponse(BaseModel):
    layout_hint: LayoutHint
    diagram_spec: DiagramSpec
