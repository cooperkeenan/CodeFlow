from placement.flow_page_placer import FlowPagePlacer
from placement.flow_page_placer_factory import build_flow_page_placer


def get_flow_page_placer() -> FlowPagePlacer:
    return build_flow_page_placer()
