from models.effect_site import EffectSite
from models.flow_entry import FlowEntry
from services.analysis.path_normalizer import normalize_out_path
from services.analysis.route_matcher import RouteMatcher
from services.analysis.route_stitch_index import RouteStitchIndex
from shared.models.flow_graph import FlowEdge


class HttpStitchDetector:
    def __init__(self, matcher: RouteMatcher) -> None:
        self._matcher = matcher

    def detect(
        self, effects: tuple[EffectSite, ...], entries: tuple[FlowEntry, ...]
    ) -> tuple[FlowEdge, ...]:
        index = RouteStitchIndex(entries)
        edges: list[FlowEdge] = []
        for effect in effects:
            if effect.kind != "http_out":
                continue
            segments = normalize_out_path(effect.target)
            if segments is None:
                continue
            match = self._matcher.match(effect.method, segments, index)
            if match is None:
                continue
            edges.append(
                FlowEdge(
                    source=effect.id,
                    target=match.entry_id,
                    kind="stitch",
                    confidence=match.confidence,
                )
            )
        return tuple(edges)
