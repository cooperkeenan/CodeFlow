from shared.models.flow_graph import FlowEdge, Lane
from placement.flow_grid_config import FlowGridConfig
from placement.flow_node_treatment import node_data, shape_for
from placement.tree_layout import NodePlacement

_DASHED_ARMS = frozenset({"except", "exception", "error"})


def build_node_dict(placement: NodePlacement, lane_id: str, arm_count: int) -> dict:
    node = placement.node
    data = node_data(node, lane_id, placement.column, placement.is_spine, arm_count)
    return {
        "id": node.id,
        "type": "flow",
        "position": {"x": placement.x, "y": placement.y},
        "kind": node.kind,
        "shape": shape_for(node, arm_count),
        "label": node.llm_label or node.label,
        "data": data,
    }


def build_header_dict(lane: Lane, center_y: int, config: FlowGridConfig) -> dict:
    return {
        "id": f"lane:{lane.id}",
        "type": "laneHeader",
        "position": {"x": 0, "y": center_y - config.row_height // 2},
        "kind": "lane_header",
        "shape": "lane_header",
        "label": lane.llm_title or lane.name,
        "data": {"laneId": lane.id, "mass": lane.mass},
    }


def build_edge_dict(edge: FlowEdge, is_spine: bool) -> dict:
    dashed = edge.confidence == "dynamic" or edge.arm_label.lower() in _DASHED_ARMS
    result: dict = {
        "id": f"{edge.source}->{edge.target}:{edge.arm_label}",
        "source": edge.source,
        "target": edge.target,
        "kind": edge.kind,
        "label": edge.llm_label or edge.arm_label,
        "isSpine": is_spine,
        "dashed": dashed,
        "confidence": edge.confidence,
        "routed": "gutter" if edge.kind == "stitch" else "lane",
    }
    if edge.kind == "stitch":
        result["targetPort"] = "entry"
    return result
