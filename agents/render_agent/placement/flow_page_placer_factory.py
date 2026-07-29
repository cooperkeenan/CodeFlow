from placement.flow_grid_config import FlowGridConfig
from placement.flow_page_placer import FlowPagePlacer
from placement.lane_layout import LaneLayout
from placement.lane_packer import LanePacker
from placement.spine_router import SpineRouter


def build_flow_page_placer() -> FlowPagePlacer:
    config = FlowGridConfig()
    return FlowPagePlacer(config, SpineRouter(), LanePacker(), LaneLayout(config))
