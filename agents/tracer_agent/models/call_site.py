from dataclasses import dataclass

from models.control_frame import ControlFrame
from models.resolved_target import ResolvedTarget


@dataclass(frozen=True)
class CallSite:
    caller: str
    line: int
    targets: tuple[ResolvedTarget, ...]
    context: tuple[ControlFrame, ...]
    in_loop: bool
    call_source: str
