from dataclasses import dataclass

from services.analysis.flow_event import FlowEvent


@dataclass(frozen=True)
class CollectedEvents:
    leaves: tuple[FlowEvent, ...]
    decisions: tuple[FlowEvent, ...]
    guarded_ids: frozenset[str]
    decision_prefix: dict[str, tuple[tuple[str, int], ...]]
    file: str
