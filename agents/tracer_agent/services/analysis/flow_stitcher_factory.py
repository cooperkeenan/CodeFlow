from services.analysis.flow_stitcher import FlowStitcher
from services.analysis.http_stitch_detector import HttpStitchDetector
from services.analysis.route_matcher import RouteMatcher


def build_flow_stitcher() -> FlowStitcher:
    return FlowStitcher((HttpStitchDetector(RouteMatcher()),))
