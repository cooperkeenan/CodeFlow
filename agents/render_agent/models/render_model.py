from pydantic import BaseModel

from shared.models.diagram_template import DiagramTemplate, RenderedView


class RenderRequest(BaseModel):
    diagram_templates: dict[str, DiagramTemplate]


class RenderResponse(BaseModel):
    views: dict[str, RenderedView]
