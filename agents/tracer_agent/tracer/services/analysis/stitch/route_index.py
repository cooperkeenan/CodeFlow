from dataclasses import dataclass

from tracer.models.sites import FlowEntry
from tracer.services.analysis.syntax.paths import is_placeholder, split_segments

from shared.models.flow_graph import Confidence


@dataclass(frozen=True)
class RouteArm:
    entry_id: str
    segments: tuple[str, ...]


@dataclass(frozen=True)
class StitchMatch:
    entry_id: str
    confidence: Confidence


class RouteStitchIndex:
    def __init__(self, entries: tuple[FlowEntry, ...]) -> None:
        by_method: dict[str, list[RouteArm]] = {}
        for entry in entries:
            if not entry.method or not entry.path:
                continue
            by_method.setdefault(entry.method, []).append(
                RouteArm(entry.id, split_segments(entry.path))
            )
        self._by_method = by_method

    def arms_for(self, method: str) -> tuple[RouteArm, ...]:
        return tuple(self._by_method.get(method, ()))


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
