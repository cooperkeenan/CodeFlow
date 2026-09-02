from dataclasses import dataclass, field
from typing import Any, Literal

from shared.models.flow_graph import Badge, EdgeKind, EffectKind, NodeKind, SourceRef

EventKind = Literal["call", "effect", "decision", "parallel"]

_PRIORITY: dict[str, int] = {"call": 0, "parallel": 1, "decision": 2, "effect": 3}


@dataclass(frozen=True)
class FlowEvent:
    kind: EventKind
    line: int
    path: tuple[tuple[str, int], ...]
    payload: Any

    @property
    def sort_key(self) -> tuple[int, int, str]:
        return (self.line, _PRIORITY[self.kind], str(getattr(self.payload, "id", self.payload)))


@dataclass(frozen=True)
class CollectedEvents:
    leaves: tuple[FlowEvent, ...]
    decisions: tuple[FlowEvent, ...]
    guarded_ids: frozenset[str]
    decision_prefix: dict[str, tuple[tuple[str, int], ...]]
    file: str


@dataclass
class _NodeDraft:
    id: str
    kind: NodeKind
    lane: str
    label: str
    backing: list[str] = field(default_factory=list)
    refs: list[SourceRef] = field(default_factory=list)
    badges: set[Badge] = field(default_factory=set)
    effect_kind: EffectKind | None = None
    effect_target: str = ""
    folded_count: int = 0
    owner_fqn: str = ""
    arm_path: list[str] = field(default_factory=list)
    containers: list[str] = field(default_factory=list)


@dataclass
class _EdgeDraft:
    source: str
    target: str
    kind: EdgeKind
    arm_label: str = ""
    group_id: str = ""
    confidence: str = "resolved"
