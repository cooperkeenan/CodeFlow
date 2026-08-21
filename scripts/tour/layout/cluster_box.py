from dataclasses import dataclass


@dataclass(frozen=True)
class ClusterBox:
    offsets: dict[str, tuple[int, int]]
    width: int
    height: int
