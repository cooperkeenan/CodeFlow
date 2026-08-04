from dataclasses import dataclass


@dataclass(frozen=True)
class ReviewFinding:
    node_id: str
    issue: str
