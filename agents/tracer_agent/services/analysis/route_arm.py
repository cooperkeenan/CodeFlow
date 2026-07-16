from dataclasses import dataclass


@dataclass(frozen=True)
class RouteArm:
    entry_id: str
    segments: tuple[str, ...]
