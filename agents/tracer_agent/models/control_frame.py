from dataclasses import dataclass
from typing import Literal


@dataclass(frozen=True)
class ControlFrame:
    kind: Literal["if", "match", "try", "loop", "with"]
    site_id: str
    arm_index: int
