from shared.models.node_geometry import NodeGeometry

from tour.layout._row_math import row_positions, total_row_width
from tour.layout.cluster_box import ClusterBox
from tour.layout.layout_constants import ARM_GAP_X, ARM_GAP_Y, BEAT_GAP_Y
from tour.tour_beat import Beat

TARGET_ASPECT = 2.1
MAX_ROW_WIDTH = 1560


class GridArrangement:
    def arrange(self, beat: Beat, geometry: dict[str, NodeGeometry]) -> ClusterBox:
        beat_geometry = geometry[beat.id]
        arm_ids = [arm.id for arm in beat.arms]
        columns = self._choose_columns(arm_ids, geometry, beat_geometry.height)
        rows = [arm_ids[index:index + columns] for index in range(0, len(arm_ids), columns)]
        row_widths, row_heights = self._row_metrics(rows, geometry)
        cluster_width = max(beat_geometry.width, max(row_widths))
        cluster_height = (
            beat_geometry.height + BEAT_GAP_Y + sum(row_heights) + ARM_GAP_Y * (len(rows) - 1)
        )
        offsets = {beat.id: ((cluster_width - beat_geometry.width) // 2, 0)}
        y = beat_geometry.height + BEAT_GAP_Y
        for row, row_width, row_height in zip(rows, row_widths, row_heights):
            widths = [geometry[arm_id].width for arm_id in row]
            start_x = (cluster_width - row_width) // 2
            for arm_id, x in zip(row, row_positions(widths, ARM_GAP_X)):
                offsets[arm_id] = (start_x + x, y)
            y += row_height + ARM_GAP_Y
        return ClusterBox(offsets=offsets, width=cluster_width, height=cluster_height)

    def _row_metrics(
        self, rows: list[list[str]], geometry: dict[str, NodeGeometry],
    ) -> tuple[list[int], list[int]]:
        row_widths = [
            total_row_width([geometry[arm_id].width for arm_id in row], ARM_GAP_X) for row in rows
        ]
        row_heights = [max(geometry[arm_id].height for arm_id in row) for row in rows]
        return row_widths, row_heights

    def _choose_columns(
        self, arm_ids: list[str], geometry: dict[str, NodeGeometry], beat_height: int,
    ) -> int:
        best_columns, best_penalty = len(arm_ids), None
        for columns in range(2, len(arm_ids) + 1):
            rows = [arm_ids[index:index + columns] for index in range(0, len(arm_ids), columns)]
            row_widths, row_heights = self._row_metrics(rows, geometry)
            widest = max(row_widths)
            if widest > MAX_ROW_WIDTH:
                continue
            height = beat_height + BEAT_GAP_Y + sum(row_heights) + ARM_GAP_Y * (len(rows) - 1)
            penalty = abs(widest / height - TARGET_ASPECT)
            if best_penalty is None or penalty < best_penalty:
                best_penalty, best_columns = penalty, columns
        return best_columns
