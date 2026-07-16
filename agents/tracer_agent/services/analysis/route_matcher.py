from shared.models.flow_graph import Confidence

from services.analysis.path_normalizer import is_placeholder
from services.analysis.route_stitch_index import RouteStitchIndex
from services.analysis.stitch_match import StitchMatch


class RouteMatcher:
    def match(
        self, method: str, out_segments: tuple[str, ...], index: RouteStitchIndex
    ) -> StitchMatch | None:
        arms = index.arms_for(method)
        full = [arm for arm in arms if self._full_match(out_segments, arm.segments)]
        if len(full) == 1:
            return StitchMatch(full[0].entry_id, self._confidence(out_segments, full[0].segments))
        if len(full) > 1:
            return None
        suffix = [arm for arm in arms if self._suffix_match(out_segments, arm.segments)]
        if len(suffix) == 1:
            return StitchMatch(suffix[0].entry_id, "inferred")
        return None

    def _full_match(self, out: tuple[str, ...], route: tuple[str, ...]) -> bool:
        if not out or len(out) != len(route):
            return False
        return all(self._segment_match(o, r) for o, r in zip(out, route))

    def _suffix_match(self, out: tuple[str, ...], route: tuple[str, ...]) -> bool:
        if not out or len(out) >= len(route):
            return False
        tail = route[len(route) - len(out):]
        return all(self._segment_match(o, r) for o, r in zip(out, tail))

    def _segment_match(self, out_seg: str, route_seg: str) -> bool:
        if is_placeholder(out_seg) or is_placeholder(route_seg):
            return True
        return out_seg == route_seg

    def _confidence(self, out: tuple[str, ...], route: tuple[str, ...]) -> Confidence:
        has_placeholder = any(is_placeholder(seg) for seg in out) or any(
            is_placeholder(seg) for seg in route
        )
        return "inferred" if has_placeholder else "resolved"
