from dataclasses import dataclass
from typing import Any, Literal

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
