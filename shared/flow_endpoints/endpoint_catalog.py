from shared.flow_endpoints.endpoint_items import EndpointItem
from shared.models.flow_graph import FlowGraph, FlowNode

_ENTRY_PREFIX = "entry:"
_NON_ROUTE_PREFIXES = ("entry:seed:", "entry:trivial:")


class EndpointCatalog:
    def items(self, graph: FlowGraph) -> list[EndpointItem]:
        entries = [
            node
            for node in graph.nodes
            if node.kind == "entry" and node.id.startswith(_ENTRY_PREFIX)
        ]
        return sorted(
            (self._item(node) for node in entries),
            key=lambda item: (not item.is_route, item.label.lower(), item.id),
        )

    def _item(self, node: FlowNode) -> EndpointItem:
        ref = node.refs[0] if node.refs else None
        return EndpointItem(
            id=node.id,
            label=node.label,
            title=node.llm_label or node.label,
            one_liner=node.one_liner,
            is_route=self._is_route(node.id),
            route_count=max(node.folded_count, 1) if node.id.startswith("entry:group:") else 1,
            file=ref.file if ref else "",
            line=ref.line if ref else 0,
        )

    def _is_route(self, node_id: str) -> bool:
        return not node_id.startswith(_NON_ROUTE_PREFIXES)
