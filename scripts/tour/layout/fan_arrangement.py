from shared.models.node_geometry import NodeGeometry

from tour.layout._row_math import row_positions, total_row_width
from tour.layout.cluster_box import ClusterBox
from tour.layout.layout_constants import ARM_GAP_X, BEAT_GAP_Y
from tour.tour_beat import Beat


class FanArrangement:
    def arrange(self, beat: Beat, geometry: dict[str, NodeGeometry]) -> ClusterBox:
        beat_geometry = geometry[beat.id]
        arm_ids = [arm.id for arm in beat.arms]
        widths = [geometry[arm_id].width for arm_id in arm_ids]
        heights = [geometry[arm_id].height for arm_id in arm_ids]
        row_width = total_row_width(widths, ARM_GAP_X)
        row_height = max(heights, default=0)
        cluster_width = max(beat_geometry.width, row_width)
        cluster_height = beat_geometry.height + BEAT_GAP_Y + row_height
        beat_x = (cluster_width - beat_geometry.width) // 2
        row_start_x = (cluster_width - row_width) // 2
        row_y = beat_geometry.height + BEAT_GAP_Y
        offsets = {beat.id: (beat_x, 0)}
        for arm_id, x in zip(arm_ids, row_positions(widths, ARM_GAP_X)):
            offsets[arm_id] = (row_start_x + x, row_y)
        return ClusterBox(offsets=offsets, width=cluster_width, height=cluster_height)
