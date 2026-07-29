from dataclasses import dataclass

from shared.models.flow_graph import FlowEdge, FlowNode
from placement.flow_grid_config import FlowGridConfig
from placement.flow_reach import longest_path_depths


@dataclass(frozen=True)
class NodePlacement:
    node: FlowNode
    x: int
    y: int
    column: int
    is_spine: bool


@dataclass(frozen=True)
class LaneBand:
    placements: list[NodePlacement]
    band_top: int
    band_height: int
    center_y: int


class LaneLayout:
    def __init__(self, config: FlowGridConfig) -> None:
        self._config = config

    def layout(
        self,
        lane_nodes: list[FlowNode],
        edges: list[FlowEdge],
        spine_nodes: frozenset[str],
        band_top: int,
    ) -> LaneBand:
        cfg = self._config
        depths = longest_path_depths(lane_nodes, edges)
        max_col = max(depths.values(), default=0)
        columns = self._columns(lane_nodes, depths, max_col, spine_nodes)
        center_y = band_top + cfg.lane_header_height + cfg.row_height // 2
        placements: list[NodePlacement] = []
        max_rows = 1
        for column, members in columns.items():
            max_rows = max(max_rows, len(members))
            x = cfg.lane_header_width + column * cfg.col_step
            for row, node in enumerate(members):
                y = center_y + row * cfg.row_step
                placements.append(
                    NodePlacement(node, x, y, column, node.id in spine_nodes)
                )
        band_height = cfg.lane_header_height + max_rows * cfg.row_step + cfg.lane_padding
        return LaneBand(placements, band_top, band_height, center_y)

    def _columns(
        self,
        lane_nodes: list[FlowNode],
        depths: dict[str, int],
        max_col: int,
        spine_nodes: frozenset[str],
    ) -> dict[int, list[FlowNode]]:
        buckets: dict[int, list[FlowNode]] = {}
        for node in lane_nodes:
            column = max_col if node.kind == "effect" else depths.get(node.id, 0)
            buckets.setdefault(column, []).append(node)
        for column in buckets:
            buckets[column].sort(key=lambda n: (n.id not in spine_nodes, n.id))
        return dict(sorted(buckets.items()))
