from services.cluster_renderer import ClusterRenderer
from services.edge_renderer import EdgeRenderer
from services.mermaid_service import MermaidService
from services.module_renderer import ModuleRenderer


def get_mermaid_service() -> MermaidService:
    return MermaidService(ModuleRenderer(ClusterRenderer()), EdgeRenderer())
