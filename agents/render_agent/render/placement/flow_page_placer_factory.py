from render.placement.flow_grid_config import FlowGridConfig
from render.placement.flow_page_placer import FlowPagePlacer
from render.placement.hidden_emitter import HiddenEmitter
from render.placement.lane_packer import LanePacker
from render.placement.spine_router import SpineRouter
from render.placement.tree_layout import TreeLayout


def build_flow_page_placer() -> FlowPagePlacer:
    config = FlowGridConfig()
    return FlowPagePlacer(
        config, SpineRouter(), LanePacker(), TreeLayout(config), HiddenEmitter(config)
    )
