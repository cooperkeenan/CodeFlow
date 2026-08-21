import math

from shared.models.node_geometry import NodeGeometry

from tour.layout._row_math import row_positions, total_row_width
from tour.layout.cluster_box import ClusterBox
from tour.layout.layout_constants import ARM_GAP_X, BEAT_GAP_Y
from tour.tour_beat import Beat

LIFT = 46
ARC_SPAN = math.pi / 3


class ArcArrangement:
    def arrange(self, beat: Beat, geometry: dict[str, NodeGeometry]) -> ClusterBox:
        beat_geometry = geometry[beat.id]
        arm_ids = [arm.id for arm in beat.arms]
        widths = [geometry[arm_id].width for arm_id in arm_ids]
        heights = [geometry[arm_id].height for arm_id in arm_ids]
        row_width = total_row_width(widths, ARM_GAP_X)
        base_y = beat_geometry.height + BEAT_GAP_Y
        ys = [base_y - lift for lift in self._lifts(len(arm_ids))]
        cluster_width = max(beat_geometry.width, row_width)
        cluster_height = max(
            [beat_geometry.height] + [y + h for y, h in zip(ys, heights)]
        )
        beat_x = (cluster_width - beat_geometry.width) // 2
        row_start_x = (cluster_width - row_width) // 2
        offsets = {beat.id: (beat_x, 0)}
        xs = row_positions(widths, ARM_GAP_X)
        for arm_id, x, y in zip(arm_ids, xs, ys):
            offsets[arm_id] = (row_start_x + x, y)
        return ClusterBox(offsets=offsets, width=cluster_width, height=cluster_height)

    def _lifts(self, count: int) -> list[int]:
        if count == 1:
            return [0]
        return [
            round(LIFT * (1 - math.cos(-ARC_SPAN + index * (2 * ARC_SPAN) / (count - 1))))
            for index in range(count)
        ]
