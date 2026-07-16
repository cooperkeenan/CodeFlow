from dataclasses import dataclass

from models.control_frame import ControlFrame
from shared.models.flow_graph import EffectKind


@dataclass(frozen=True)
class EffectSite:
    id: str
    owner: str
    kind: EffectKind
    target: str
    method: str
    line: int
    context: tuple[ControlFrame, ...]
