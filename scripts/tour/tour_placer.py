import math

from shared.models.diagram_template import RenderedView
from shared.models.flow_graph import FlowGraph
from shared.models.node_geometry import geometry_for, geometry_payload

from placement.flow_node_treatment import node_data, shape_for

from tour.tour_beat import Beat

CENTER_X = 1200
SIDE_OFFSET = 520
ROW_STEP = 200
TOP_MARGIN = 120
HEADER_X = 120
WAVE_AMPLITUDE = 230
WAVE_BEATS = 9.0


class TourPlacer:
    def __init__(self, center_x: int = CENTER_X, row_step: int = ROW_STEP) -> None:
        self._center_x = center_x
        self._row_step = row_step

    def place(self, graph: FlowGraph, beats: list[Beat]) -> RenderedView:
        rows = self._rows(beats)
        arm_counts = self._arm_counts(graph)
        nodes_by_id = {node.id: node for node in graph.nodes}
        centres = self._centres(beats)
        spine_ids = {beat.id for beat in beats}
        out_nodes = [
            self._node_dict(
                nodes_by_id[node_id], centre_x, rows[node_id], arm_counts,
                node_id in spine_ids,
            )
            for node_id, centre_x in centres.items()
        ]
        out_nodes.extend(self._headers(graph, beats, rows))
        out_edges = [self._edge_dict(edge) for edge in graph.edges]
        out_nodes.sort(key=lambda item: item["id"])
        out_edges.sort(key=lambda item: item["id"])
        return RenderedView(
            type="flow", page_title=graph.page_title, nodes=out_nodes, edges=out_edges,
            hidden=[], hidden_edges=[], node_geometry=geometry_payload(),
        )

    def _rows(self, beats: list[Beat]) -> dict[str, int]:
        rows: dict[str, int] = {}
        cursor = 0
        for beat in beats:
            rows[beat.id] = cursor
            cursor += 1
            for index, arm in enumerate(beat.arms):
                rows[arm.id] = cursor + index // 2
            if beat.arms:
                cursor += (len(beat.arms) + 1) // 2
        return rows

    def _spine_x(self, position: int) -> int:
        return round(
            self._center_x + WAVE_AMPLITUDE * math.sin(2 * math.pi * position / WAVE_BEATS)
        )

    def _centres(self, beats: list[Beat]) -> dict[str, int]:
        centres: dict[str, int] = {}
        for position, beat in enumerate(beats):
            centre = self._spine_x(position)
            centres[beat.id] = centre
            for index, arm in enumerate(beat.arms):
                side = -1 if index % 2 == 0 else 1
                centres[arm.id] = centre + side * SIDE_OFFSET
        return centres

    def _arm_counts(self, graph: FlowGraph) -> dict[str, int]:
        counts: dict[str, int] = {}
        for edge in graph.edges:
            if edge.kind == "arm":
                counts[edge.source] = counts.get(edge.source, 0) + 1
        return counts

    def _node_dict(
        self, node, centre_x: int, row: int, arm_counts: dict[str, int], is_spine: bool,
    ) -> dict:
        count = arm_counts.get(node.id, 0)
        shape = shape_for(node, count)
        geometry = geometry_for(shape)
        data = node_data(node, node.lane, 0, is_spine, count)
        data["hiddenChildren"] = []
        return {
            "id": node.id,
            "type": "flow",
            "position": {
                "x": centre_x - geometry.width // 2,
                "y": TOP_MARGIN + row * self._row_step,
            },
            "kind": node.kind,
            "shape": shape,
            "label": node.llm_label or node.label,
            "data": data,
        }

    def _headers(self, graph: FlowGraph, beats: list[Beat], rows: dict[str, int]) -> list[dict]:
        first: dict[str, str] = {}
        for beat in beats:
            first.setdefault(beat.lane, beat.id)
        return [
            {
                "id": f"lane:{lane.id}",
                "type": "laneHeader",
                "position": {
                    "x": HEADER_X,
                    "y": TOP_MARGIN + rows[first[lane.id]] * self._row_step,
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
