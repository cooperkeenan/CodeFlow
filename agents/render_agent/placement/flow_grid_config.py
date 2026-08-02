from dataclasses import dataclass


@dataclass(frozen=True)
class FlowGridConfig:
    column_width: int = 200
    row_height: int = 72
    column_gutter: int = 120
    row_gutter: int = 32
    lane_gutter: int = 80
    lane_header_width: int = 220
    lane_header_height: int = 44
    lane_padding: int = 40
    subtree_gap_rows: int = 1

    @property
    def col_step(self) -> int:
        return self.column_width + self.column_gutter

    @property
    def row_step(self) -> int:
        return self.row_height + self.row_gutter
