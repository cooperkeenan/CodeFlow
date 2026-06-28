import logging

from placement.registry import PlacementRegistry
from shared.models.diagram_template import DiagramTemplate, RenderedView

logger = logging.getLogger(__name__)

_SYSTEM_PREFIX = "mod__"


class PlacementService:
    def __init__(self, registry: PlacementRegistry) -> None:
        self._registry = registry

    def render(self, templates: dict[str, DiagramTemplate]) -> dict[str, RenderedView]:
        views: dict[str, RenderedView] = {}
        for view_id, template in templates.items():
            if view_id.startswith("module:"):
                place_key = "zoned" if template.type == "zoned" else f"component_{template.type}"
            elif view_id.startswith("component:"):
                place_key = f"component_{template.type}"
            else:
                place_key = template.type
            place = self._registry.get(place_key)
            nodes = place(template)
            if view_id == "system":
                self._apply_counts(nodes, template)
            if view_id.startswith("component:"):
                self._apply_descriptions(nodes, template)
            edges = self._build_edges(template, view_id)
            views[view_id] = RenderedView(type=template.type, nodes=nodes, edges=edges)
            logger.debug("Placed view=%s type=%s nodes=%d", view_id, template.type, len(nodes))
        return views

    def _apply_counts(self, nodes: list[dict], template: DiagramTemplate) -> None:
        counts = {
            f"{_SYSTEM_PREFIX}{n.module_name}": (n.zone_count, n.component_count)
            for n in template.nodes
        }
        for node in nodes:
            entry = counts.get(node.get("id"))
            if entry:
                node["data"]["zoneCount"], node["data"]["componentCount"] = entry

    def _apply_descriptions(self, nodes: list[dict], template: DiagramTemplate) -> None:
        focus = template.meta.get("focus")
        if not focus:
            return
        desc_map = {n.id: n.description for n in template.nodes}
        desc = desc_map.get(focus, "")
        if not desc:
            return
        for node in nodes:
            if node.get("id") == focus:
                node["data"]["description"] = desc
                break

    def _build_edges(self, template: DiagramTemplate, view_id: str) -> list[dict]:
        is_system = view_id == "system"
        edges: list[dict] = []
        for e in template.edges:
            src = f"{_SYSTEM_PREFIX}{e.source}" if is_system else e.source
            tgt = f"{_SYSTEM_PREFIX}{e.target}" if is_system else e.target
            edge: dict = {"id": f"{src}->{tgt}", "source": src, "target": tgt, "edge_type": e.edge_type}
            if e.edge_type not in ("call", "sequence"):
                edge["label"] = e.edge_type
            edges.append(edge)
        return edges
