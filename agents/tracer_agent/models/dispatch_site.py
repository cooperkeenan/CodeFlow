from dataclasses import dataclass
from typing import Literal

from models.arm import Arm
from shared.models.flow_graph import SourceRef

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
