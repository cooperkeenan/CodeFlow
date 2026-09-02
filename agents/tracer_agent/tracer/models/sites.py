from dataclasses import dataclass, field
from typing import Literal

from tracer.models.call_records import Arm, ControlFrame

from shared.models.flow_graph import EffectKind, SourceRef

DispatchKind = Literal["branch", "match", "table", "route", "polymorphic", "except", "dynamic"]


@dataclass(frozen=True)
class DispatchSite:
    id: str
    owner: str
    kind: DispatchKind
    selector_source: str
    selector_reads: tuple[str, ...]
    arms: tuple[Arm, ...]
    reconverges: bool
    span: SourceRef


@dataclass(frozen=True)
class ParallelSite:
    id: str
    owner: str
    line: int
    callees: tuple[str, ...]
    span: SourceRef


@dataclass(frozen=True)
class EffectSite:
    id: str
    owner: str
    kind: EffectKind
    target: str
    method: str
    line: int
    context: tuple[ControlFrame, ...]


@dataclass(frozen=True)
class FlowEntry:
    id: str
    handler_fqn: str
    label: str
    service_root: str
    method: str = ""
    path: str = ""
    members: tuple[str, ...] = field(default_factory=tuple)
    route_count: int = 1
