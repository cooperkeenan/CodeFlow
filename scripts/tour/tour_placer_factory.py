from tour.layout.arrangement_factory import build_arrangement_picker
from tour.layout.cluster_stacker import ClusterStacker
from tour.tour_placer import TourPlacer


def build_tour_placer() -> TourPlacer:
    return TourPlacer(build_arrangement_picker(), ClusterStacker())
