from shared.models.diagram_template import RenderedView
from shared.models.flow_graph import FlowGraph, FlowNode
from placement.flow_emit import build_edge_dict, build_header_dict, build_node_dict
from placement.flow_grid_config import FlowGridConfig
from placement.lane_layout import LaneLayout
from placement.lane_packer import LanePacker
from placement.spine_router import SpineRouter


class FlowPagePlacer:
    def __init__(
        self,
        config: FlowGridConfig,
        spine_router: SpineRouter,
        lane_packer: LanePacker,
        lane_layout: LaneLayout,
    ) -> None:
        self._config = config
        self._spine_router = spine_router
        self._lane_packer = lane_packer
        self._lane_layout = lane_layout

    def place(self, graph: FlowGraph) -> RenderedView:
        spine = self._spine_router.route(graph)
        order = self._lane_packer.order(graph)
        arm_counts = self._arm_counts(graph)
        lanes_by_id = {lane.id: lane for lane in graph.lanes}
        nodes_by_lane = self._group_by_lane(graph.nodes)

        out_nodes: list[dict] = []
        band_top = 0
        for lane_id in order:
            lane_nodes = nodes_by_lane.get(lane_id, [])
            band = self._lane_layout.layout(
                lane_nodes, graph.edges, spine.node_ids, band_top
            )
            lane = lanes_by_id.get(lane_id)
            if lane is not None:
                out_nodes.append(build_header_dict(lane, band.center_y, self._config))
            for placement in band.placements:
                out_nodes.append(
                    build_node_dict(
                        placement, lane_id, arm_counts.get(placement.node.id, 0)
                    )
                )
            band_top += band.band_height + self._config.lane_gutter

        out_edges = [
            build_edge_dict(
                edge, (edge.source, edge.target, edge.arm_label) in spine.edge_keys
            )
            for edge in graph.edges
        ]
        out_nodes.sort(key=lambda node: node["id"])
        out_edges.sort(key=lambda edge: edge["id"])
        return RenderedView(type="flow", nodes=out_nodes, edges=out_edges)

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
