from shared.models.diagram_template import RenderedView
from shared.models.flow_graph import FlowGraph, FlowNode
from shared.models.node_geometry import geometry_payload
from placement.flow_emit import build_edge_dict, build_header_dict, build_node_dict
from placement.flow_grid_config import FlowGridConfig
from placement.hidden_emitter import HiddenEmitter
from placement.lane_packer import LanePacker
from placement.spine_router import SpineRouter
from placement.tree_layout import TreeLayout


class FlowPagePlacer:
    def __init__(
        self,
        config: FlowGridConfig,
        spine_router: SpineRouter,
        lane_packer: LanePacker,
        tree_layout: TreeLayout,
        hidden_emitter: HiddenEmitter,
    ) -> None:
        self._config = config
        self._spine_router = spine_router
        self._lane_packer = lane_packer
        self._tree_layout = tree_layout
        self._hidden = hidden_emitter

    def place(self, graph: FlowGraph) -> RenderedView:
        spine = self._spine_router.route(graph)
        order = self._lane_packer.order(graph)
        arm_counts = self._arm_counts(graph)
        lanes_by_id = {lane.id: lane for lane in graph.lanes}
        skeleton_ids = frozenset(node.id for node in graph.nodes if node.level == 0)
        skeleton_edges = [
            edge
            for edge in graph.edges
            if edge.source in skeleton_ids and edge.target in skeleton_ids
        ]
        nodes_by_lane = self._group_by_lane(
            [node for node in graph.nodes if node.level == 0]
        )

        out_nodes: list[dict] = []
        placed: list[tuple[str, dict, FlowNode]] = []
        tree_pairs: set[tuple[str, str]] = set()
        band_top = 0
        for lane_id in order:
            lane_nodes = nodes_by_lane.get(lane_id, [])
            band = self._tree_layout.layout(
                lane_nodes, skeleton_edges, spine.node_ids, band_top
            )
            tree_pairs |= band.tree_pairs
            lane = lanes_by_id.get(lane_id)
            if lane is not None:
                out_nodes.append(build_header_dict(lane, band.center_y, self._config))
            for placement in band.placements:
                node_dict = build_node_dict(
                    placement, lane_id, arm_counts.get(placement.node.id, 0)
                )
                out_nodes.append(node_dict)
                placed.append((placement.node.id, node_dict, placement.node))
            band_top += band.band_height + self._config.lane_gutter

        for _, node_dict, node in placed:
            node_dict["data"]["hiddenChildren"] = self._hidden.offsets(node)

        out_edges = []
        for edge in skeleton_edges:
            edge_dict = build_edge_dict(edge, False)
            edge_dict["secondary"] = (edge.source, edge.target) not in tree_pairs
            out_edges.append(edge_dict)
        out_nodes.sort(key=lambda node: node["id"])
        out_edges.sort(key=lambda edge: edge["id"])
        return RenderedView(
            type="flow",
            nodes=out_nodes,
            edges=out_edges,
            hidden=self._hidden.payloads(graph, arm_counts),
            hidden_edges=self._hidden.edges(graph, skeleton_ids),
            node_geometry=geometry_payload(),
        )

    def _arm_counts(self, graph: FlowGraph) -> dict[str, int]:
        counts: dict[str, int] = {}
        for edge in graph.edges:
            if edge.kind == "arm":
                counts[edge.source] = counts.get(edge.source, 0) + 1
        return counts

    def _group_by_lane(self, nodes: list[FlowNode]) -> dict[str, list[FlowNode]]:
        grouped: dict[str, list[FlowNode]] = {}
        for node in nodes:
            grouped.setdefault(node.lane, []).append(node)
        return grouped
