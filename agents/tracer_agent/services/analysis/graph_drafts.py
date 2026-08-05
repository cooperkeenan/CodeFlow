from dataclasses import dataclass, field

from shared.models.flow_graph import Badge, EdgeKind, EffectKind, NodeKind, SourceRef


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
