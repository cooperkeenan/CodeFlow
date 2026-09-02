from dataclasses import dataclass


@dataclass(frozen=True)
class FlowSummary:
    head: str | None
    tails: tuple[str, ...]
    recursive: bool = False
