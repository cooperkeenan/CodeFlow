import logging

from services.edge_renderer import EdgeRenderer
from services.module_renderer import ModuleRenderer

from shared.models.diagram_spec import DiagramSpec

logger = logging.getLogger(__name__)


class MermaidService:
    def __init__(self, module_renderer: ModuleRenderer, edge_renderer: EdgeRenderer):
        self._modules = module_renderer
        self._edges = edge_renderer

    def render(self, spec: DiagramSpec) -> str:
        logger.info("Rendering %s diagram, %d modules", spec.architecture_type, len(spec.modules))
        lines = ["flowchart TD"]
        lines += self._modules.render_actors(spec.external_actors)
        lines += self._modules.render(spec)
        lines += self._edges.render(spec)
        diagram = "\n".join(lines)
        logger.info("Diagram complete: %d lines", len(lines))
        return diagram
