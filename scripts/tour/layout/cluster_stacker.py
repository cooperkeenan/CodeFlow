import math

from shared.models.node_geometry import NODE_GEOMETRY

from tour.layout.cluster_box import ClusterBox
from tour.tour_beat import Beat

CLUSTER_GAP = 150
TOP_MARGIN = 120
HEADER_X = 120
WAVE_AMPLITUDE = 160
WAVE_BEATS = 9.0
_HEADER_GUTTER = 40
ACT_MARGIN = HEADER_X + NODE_GEOMETRY["lane_header"].width + _HEADER_GUTTER


class ClusterStacker:
    def __init__(self) -> None:
        self.column_bases: dict[int, int] = {}

    def place(
        self, clusters: dict[str, ClusterBox], groups: list[tuple[str, list[Beat]]],
    ) -> dict[str, tuple[int, int]]:
        widest = max((cluster.width for cluster in clusters.values()), default=0)
        act_pitch = widest + ACT_MARGIN
        self.column_bases = {index: index * act_pitch for index in range(len(groups))}
        positions: dict[str, tuple[int, int]] = {}
        beat_index = 0
        for group_index, (_, beats) in enumerate(groups):
            centre_x = self.column_bases[group_index] + ACT_MARGIN + widest // 2
            y = TOP_MARGIN
            for beat in beats:
                cluster = clusters[beat.id]
                jitter = round(
                    WAVE_AMPLITUDE * math.sin(2 * math.pi * beat_index / WAVE_BEATS)
                )
                x0 = centre_x + jitter - cluster.width // 2
                for node_id, (offset_x, offset_y) in cluster.offsets.items():
                    positions[node_id] = (x0 + offset_x, y + offset_y)
                y += cluster.height + CLUSTER_GAP
                beat_index += 1
        return positions
