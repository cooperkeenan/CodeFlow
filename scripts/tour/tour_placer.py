from shared.models.diagram_template import RenderedView
from shared.models.flow_graph import FlowGraph

from render.placement.flow_node_treatment import node_data, shape_for

from tour.layout.arrangement_picker import ArrangementPicker
from tour.layout.cluster_box import ClusterBox
from tour.layout.cluster_stacker import ClusterStacker
from tour.tour_beat import Beat
from tour.tour_card_beats import CARD_ID_PREFIX
from tour.tour_geometry import tour_geometry_for, tour_geometry_payload

HEADER_X = 120
CARD_SHAPE = "card"
SNIPPET_SHAPE = "snippet"


class TourPlacer:
    def __init__(self, picker: ArrangementPicker, stacker: ClusterStacker) -> None:
        self._picker = picker
        self._stacker = stacker
        self.clusters: dict[str, ClusterBox] = {}

    def place(
        self, graph: FlowGraph, beats: list[Beat], groups: list[tuple[str, list[Beat]]],
    ) -> RenderedView:
        arm_counts = self._arm_counts(graph)
        arm_code = self._arm_code(beats)
        nodes_by_id = {node.id: node for node in graph.nodes}
        shapes = {
            node_id: self._shape_for(nodes_by_id[node_id], node_id, arm_counts, arm_code)
            for beat in beats
            for node_id in [beat.id, *(arm.id for arm in beat.arms)]
        }
        geometry = {node_id: tour_geometry_for(shape) for node_id, shape in shapes.items()}
        self.clusters = {
            beat.id: self._picker.pick(beat).arrange(beat, geometry) for beat in beats
        }
        positions = self._stacker.place(self.clusters, groups)
        spine_ids = {beat.id for beat in beats}
        act_of = {
            beat.id: group_index
            for group_index, (_, group_beats) in enumerate(groups)
            for beat in group_beats
        }
        out_nodes = [
            self._node_dict(
                nodes_by_id[node_id], pos, shapes[node_id], arm_counts,
                node_id in spine_ids, act_of, len(groups), arm_code.get(node_id),
            )
            for node_id, pos in positions.items()
        ]
        out_nodes.extend(self._headers(graph, groups, positions))
        out_edges = [self._edge_dict(edge) for edge in graph.edges]
        out_nodes.sort(key=lambda item: item["id"])
        out_edges.sort(key=lambda item: item["id"])
        return RenderedView(
            type="flow", page_title=graph.page_title, nodes=out_nodes, edges=out_edges,
            hidden=[], hidden_edges=[], node_geometry=tour_geometry_payload(),
        )

    ArmCode = dict[str, tuple[str, str]]

    def _shape_for(self, node, node_id: str, arm_counts: dict[str, int], arm_code: ArmCode) -> str:
        if node_id.startswith(CARD_ID_PREFIX):
            return CARD_SHAPE
        if node_id in arm_code:
            return SNIPPET_SHAPE
        return shape_for(node, arm_counts.get(node_id, 0))

    def _arm_counts(self, graph: FlowGraph) -> dict[str, int]:
        counts: dict[str, int] = {}
        for edge in graph.edges:
            if edge.kind == "arm":
                counts[edge.source] = counts.get(edge.source, 0) + 1
        return counts

    def _arm_code(self, beats: list[Beat]) -> ArmCode:
        return {arm.id: (arm.code, arm.code_lang) for beat in beats for arm in beat.arms if arm.code}

    def _node_dict(
        self, node, pos: tuple[int, int], shape: str, arm_counts: dict[str, int], is_spine: bool,
        act_of: dict[str, int], act_total: int, code_info: tuple[str, str] | None = None,
    ) -> dict:
        count = arm_counts.get(node.id, 0)
        data = node_data(node, node.lane, 0, is_spine, count)
        data["hiddenChildren"] = []
        data["shape"] = shape
        if shape == CARD_SHAPE:
            data["actNumber"] = act_of[node.id] + 1
            data["actTotal"] = act_total
        if code_info is not None:
            data["code"] = code_info[0]
            data["codeLang"] = code_info[1]
        return {
            "id": node.id,
            "type": "flow",
            "position": {"x": pos[0], "y": pos[1]},
            "kind": node.kind,
            "shape": shape,
            "label": node.llm_label or node.label,
            "data": data,
        }

    def _headers(
        self,
        graph: FlowGraph,
        groups: list[tuple[str, list[Beat]]],
        positions: dict[str, tuple[int, int]],
    ) -> list[dict]:
        first: dict[str, str] = {}
        group_of: dict[str, int] = {}
        for group_index, (_, beats) in enumerate(groups):
            for beat in beats:
                if beat.lane not in first:
                    first[beat.lane] = beat.id
                    group_of[beat.lane] = group_index
        return [
            {
                "id": f"lane:{lane.id}",
                "type": "laneHeader",
                "position": {
                    "x": self._stacker.column_bases[group_of[lane.id]] + HEADER_X,
                    "y": positions[first[lane.id]][1],
                },
                "kind": "lane_header",
                "shape": "lane_header",
                "label": lane.llm_title or lane.name,
                "data": {"laneId": lane.id, "mass": lane.mass},
            }
            for lane in graph.lanes
            if lane.id in first
        ]

    def _edge_dict(self, edge) -> dict:
        return {
            "id": f"{edge.source}->{edge.target}:{edge.arm_label}",
            "source": edge.source,
            "target": edge.target,
            "kind": edge.kind,
            "label": edge.arm_label,
            "isSpine": edge.is_spine,
            "dashed": False,
            "confidence": edge.confidence,
            "routed": "lane",
            "hiddenPath": [],
            "secondary": False,
        }
