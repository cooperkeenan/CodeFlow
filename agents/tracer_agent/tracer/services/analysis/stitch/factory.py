from pathlib import Path

import anthropic
from tracer.services.analysis.contracts import StitchDetector
from tracer.services.analysis.stitch.flow_stitcher import FlowStitcher
from tracer.services.analysis.stitch.http_stitch_detector import HttpStitchDetector
from tracer.services.analysis.stitch.llm_stitch_detector import LlmStitchDetector
from tracer.services.analysis.stitch.route_index import RouteMatcher
from tracer.services.analysis.stitch.stitch_verdict_cache import StitchVerdictCache

_PARENTS = Path(__file__).resolve().parents
_ROOT = _PARENTS[4] if len(_PARENTS) > 4 else _PARENTS[2]
_DEFAULT_CACHE_PATH = _ROOT / ".cache" / "stitch_verdicts.json"


def build_flow_stitcher(api_key: str | None, cache_path: Path | None = None) -> FlowStitcher:
    detectors: tuple[StitchDetector, ...] = (HttpStitchDetector(RouteMatcher()),)
    if not api_key:
        return FlowStitcher(detectors)
    client = anthropic.Anthropic(api_key=api_key)
    cache = StitchVerdictCache(cache_path or _DEFAULT_CACHE_PATH)
    return FlowStitcher(detectors + (LlmStitchDetector(client, cache),))
