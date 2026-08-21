from typing import Protocol

from shared.models.node_geometry import NodeGeometry

from tour.layout.cluster_box import ClusterBox
from tour.tour_beat import Beat


class ArmArrangement(Protocol):
    def arrange(self, beat: Beat, geometry: dict[str, NodeGeometry]) -> ClusterBox: ...
