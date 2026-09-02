from dataclasses import dataclass
from typing import Literal


@dataclass(frozen=True)
class ControlFrame:
    kind: Literal["if", "match", "try", "loop", "with"]
    site_id: str
    arm_index: int


@dataclass(frozen=True)
class ResolvedTarget:
    fqn: str
    confidence: Literal["resolved", "inferred"]


@dataclass(frozen=True)
class CallSite:
    caller: str
    line: int
    targets: tuple[ResolvedTarget, ...]
    context: tuple[ControlFrame, ...]
    in_loop: bool
    call_source: str


Terminal = Literal["returns", "raises", "continues", "falls_through"]


@dataclass(frozen=True)
class Arm:
    index: int
    label_source: str
    callsites: tuple[CallSite, ...]
    terminal: Terminal
    handler_fqn: str | None = None
