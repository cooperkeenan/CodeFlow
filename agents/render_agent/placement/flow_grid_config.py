from dataclasses import dataclass

from shared.models.node_geometry import NODE_GEOMETRY


@dataclass(frozen=True)
class FlowGridConfig:
    column_width: int = 200
    row_height: int = 72
    column_gutter: int = 120
    row_gutter: int = 32
    lane_gutter: int = 80
    lane_padding: int = 40
    lane_header_gutter: int = 24
    subtree_gap_rows: int = 0

    @property
    def lane_header_width(self) -> int:
        return NODE_GEOMETRY["lane_header"].width + self.lane_header_gutter

    @property
    def lane_header_height(self) -> int:
        return NODE_GEOMETRY["lane_header"].height

    @property
    def col_step(self) -> int:
        return max(g.width for g in NODE_GEOMETRY.values()) + self.column_gutter

    @property
    def row_step(self) -> int:
        return max(g.height for g in NODE_GEOMETRY.values()) + self.row_gutter
