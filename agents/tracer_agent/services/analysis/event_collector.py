from models.call_site import CallSite
from models.project_index import ProjectIndex
from services.analysis.anchor_index import AnchorIndex
from services.analysis.collected_events import CollectedEvents
from services.analysis.flow_event import FlowEvent


class EventCollector:
    def __init__(self, index: ProjectIndex, anchors: AnchorIndex) -> None:
        self._index = index
        self._anchors = anchors

    def collect(self, fqn: str) -> CollectedEvents:
        record = self._index.functions[fqn]
        dispatches = self._anchors.dispatches_of(fqn)
        decision_ids = frozenset(
            d.id for d in dispatches
            if d.kind != "route" and self._anchors.verdict_of(d.id) == "decision"
        )
        guarded_ids = frozenset(
            d.id for d in dispatches if self._anchors.verdict_of(d.id) == "guarded_step"
        )
        parallel_lines = frozenset(p.line for p in self._anchors.parallels_of(fqn))
        span = (record.span.line, record.span.end_line)
        leaves = self._leaves(fqn, decision_ids, parallel_lines, span)
        decisions = tuple(
            FlowEvent("decision", d.span.line, (), d)
            for d in dispatches if d.id in decision_ids
        )
        prefixes = self._decision_prefixes(decision_ids, leaves)
        return CollectedEvents(leaves, decisions, guarded_ids, prefixes, record.span.file)

    def _leaves(
        self,
        fqn: str,
        decision_ids: frozenset[str],
        parallel_lines: frozenset[int],
        span: tuple[int, int],
    ) -> tuple[FlowEvent, ...]:
        events: list[FlowEvent] = []
        for call in self._anchors.calls_of(fqn):
            if call.line in parallel_lines or not span[0] <= call.line <= span[1]:
                continue
            events.append(FlowEvent("call", call.line, self._path(call, decision_ids), call))
        for effect in self._anchors.func_effects_of(fqn):
            events.append(FlowEvent("effect", effect.line, self._path(effect, decision_ids), effect))
        for site in self._anchors.parallels_of(fqn):
            events.append(FlowEvent("parallel", site.line, (), site))
        return tuple(events)

    def _path(self, item: CallSite, decision_ids: frozenset[str]) -> tuple[tuple[str, int], ...]:
        return tuple(
            (frame.site_id, frame.arm_index)
            for frame in item.context
            if frame.site_id in decision_ids
        )

    def _decision_prefixes(
        self, decision_ids: frozenset[str], leaves: tuple[FlowEvent, ...]
    ) -> dict[str, tuple[tuple[str, int], ...]]:
        prefixes: dict[str, tuple[tuple[str, int], ...]] = {site_id: () for site_id in decision_ids}
        assigned: set[str] = set()
        for event in sorted(leaves, key=lambda e: e.sort_key):
            for position, (frame_id, _) in enumerate(event.path):
                if frame_id in decision_ids and frame_id not in assigned:
                    prefixes[frame_id] = event.path[:position]
                    assigned.add(frame_id)
        return prefixes
