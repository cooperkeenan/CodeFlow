from services.analysis.effect_detector import EffectDetector
from services.analysis.effect_matcher import CallEffectMatcher
from services.analysis.effect_route_handler import RouteHandlerInspector
from services.analysis.effect_store_surfacer import StoreEffectSurfacer
from services.analysis.effect_target_extractor import EffectTargetExtractor


def build_effect_detector() -> EffectDetector:
    return EffectDetector(
        CallEffectMatcher(EffectTargetExtractor()),
        RouteHandlerInspector(),
        StoreEffectSurfacer(),
    )
