from dataclasses import dataclass
from typing import Literal

from models.call_site import CallSite

Terminal = Literal["returns", "raises", "continues", "falls_through"]


@dataclass(frozen=True)
class Arm:
    index: int
    label_source: str
    callsites: tuple[CallSite, ...]
    terminal: Terminal
    handler_fqn: str | None = None
