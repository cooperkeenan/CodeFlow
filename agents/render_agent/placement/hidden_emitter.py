from shared.models.flow_graph import FlowGraph, FlowNode
from placement.flow_grid_config import FlowGridConfig
from placement.flow_node_treatment import node_data, shape_for

_MAX_PER_ROW = 3


class HiddenEmitter:
    def __init__(self, config: FlowGridConfig) -> None:
        self._config = config

    def offsets(self, node: FlowNode) -> list[dict]:
        children = node.hidden_children
        return [
            {"id": child_id, "dx": dx, "dy": dy}
            for child_id, (dx, dy) in zip(children, self._block(len(children)))
        ]

    def _block(self, count: int) -> list[tuple[int, int]]:
        placements: list[tuple[int, int]] = []
        for index in range(count):
            row = index // _MAX_PER_ROW
            width = min(count - row * _MAX_PER_ROW, _MAX_PER_ROW)
            span = width - 1
            column = index % _MAX_PER_ROW
            placements.append(
                (
                    round((column - span / 2) * self._config.col_step),
                    (row + 1) * self._config.row_step,
                )
            )
        return placements

    def payloads(
        self, graph: FlowGraph, arm_counts: dict[str, int], run_ids: frozenset[str] = frozenset()
    ) -> list[dict]:
        return [
            {
                "id": node.id,
                "type": "flow",
                "kind": node.kind,
                "shape": shape_for(node, arm_counts.get(node.id, 0), node.id in run_ids),
                "label": node.llm_label or node.label,
                "data": {
                    **node_data(
                        node, node.lane, 0, False, arm_counts.get(node.id, 0), node.id in run_ids
                    ),
                    "hidden": True,
                    "hiddenChildren": self.offsets(node),
                },
            }
            for node in sorted(graph.nodes, key=lambda item: item.id)
            if node.level >= 1
        ]

    def edges(self, graph: FlowGraph, skeleton_ids: frozenset[str]) -> list[dict]:
        return [
            {
                "id": f"{edge.source}->{edge.target}:{edge.arm_label}",
                "source": edge.source,
                "target": edge.target,
                "kind": edge.kind,
                "label": edge.llm_label or edge.arm_label,
                "confidence": edge.confidence,
            }
            for edge in graph.edges
            if edge.source not in skeleton_ids or edge.target not in skeleton_ids
        ]
