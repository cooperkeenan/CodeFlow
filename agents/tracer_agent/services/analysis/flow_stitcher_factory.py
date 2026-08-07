from pathlib import Path

import anthropic
from services.analysis.flow_stitcher import FlowStitcher
from services.analysis.http_stitch_detector import HttpStitchDetector
from services.analysis.llm_stitch_detector import LlmStitchDetector
from services.analysis.route_matcher import RouteMatcher
from services.analysis.stitch_detector import StitchDetector
from services.analysis.stitch_verdict_cache import StitchVerdictCache

_DEFAULT_CACHE_PATH = Path(__file__).resolve().parents[4] / ".cache" / "stitch_verdicts.json"


def build_flow_stitcher(api_key: str | None, cache_path: Path | None = None) -> FlowStitcher:
    detectors: tuple[StitchDetector, ...] = (HttpStitchDetector(RouteMatcher()),)
    if not api_key:
        return FlowStitcher(detectors)
    client = anthropic.Anthropic(api_key=api_key)
    cache = StitchVerdictCache(cache_path or _DEFAULT_CACHE_PATH)
    return FlowStitcher(detectors + (LlmStitchDetector(client, cache),))
