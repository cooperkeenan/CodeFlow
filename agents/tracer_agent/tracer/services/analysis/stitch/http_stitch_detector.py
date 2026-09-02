from tracer.models.sites import EffectSite, FlowEntry
from tracer.services.analysis.stitch.route_index import RouteMatcher, RouteStitchIndex
from tracer.services.analysis.syntax.paths import normalize_out_path

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
