from shared.models.node_geometry import NodeGeometry

from tour.layout.cluster_box import ClusterBox
from tour.tour_beat import Beat


class SoloArrangement:
    def arrange(self, beat: Beat, geometry: dict[str, NodeGeometry]) -> ClusterBox:
        beat_geometry = geometry[beat.id]
        return ClusterBox(
            offsets={beat.id: (0, 0)}, width=beat_geometry.width, height=beat_geometry.height,
        )
