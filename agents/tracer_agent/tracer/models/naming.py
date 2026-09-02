from dataclasses import dataclass

from shared.models.flow_graph import FlowNode


@dataclass(frozen=True)
class NodeNaming:
    label: str
    one_liner: str


@dataclass(frozen=True)
class NodeNameContext:
    node: FlowNode
    arm_label_sources: tuple[str, ...]
    child_labels: tuple[str, ...]


@dataclass(frozen=True)
class ReviewFinding:
    node_id: str
    issue: str


@dataclass(frozen=True)
class ReviewResult:
    corrected: dict[str, NodeNaming]
    page_title: str
    lane_titles: dict[str, str]
    findings: list[ReviewFinding]
