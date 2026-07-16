from models.flow_entry import FlowEntry
from services.analysis.path_normalizer import split_segments
from services.analysis.route_arm import RouteArm


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
