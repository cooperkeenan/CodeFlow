from tracer.services.analysis.effects.effect_detector import EffectDetector
from tracer.services.analysis.effects.effect_matcher import CallEffectMatcher
from tracer.services.analysis.effects.effect_route_handler import RouteHandlerInspector
from tracer.services.analysis.effects.effect_store_surfacer import StoreEffectSurfacer
from tracer.services.analysis.effects.effect_target_extractor import (
    EffectTargetExtractor,
)


def build_effect_detector() -> EffectDetector:
    return EffectDetector(
        CallEffectMatcher(EffectTargetExtractor()),
        RouteHandlerInspector(),
        StoreEffectSurfacer(),
    )
