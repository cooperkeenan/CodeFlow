from dataclasses import dataclass

from models.node_naming import NodeNaming
from models.review_finding import ReviewFinding


@dataclass(frozen=True)
class ReviewResult:
    corrected: dict[str, NodeNaming]
    page_title: str
    lane_titles: dict[str, str]
    findings: list[ReviewFinding]
