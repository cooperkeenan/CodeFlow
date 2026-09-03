from pathlib import Path

from tracer.models.naming import NodeNaming, ReviewFinding, ReviewResult
from tracer.services.analysis.json_cache import JsonCache


def _serialize(result: ReviewResult) -> dict:
    return {
        "corrected": {
            node_id: {"label": naming.label, "one_liner": naming.one_liner}
            for node_id, naming in result.corrected.items()
        },
        "page_title": result.page_title,
        "lane_titles": result.lane_titles,
        "findings": [{"node_id": f.node_id, "issue": f.issue} for f in result.findings],
    }


def _deserialize(value: dict) -> ReviewResult:
    return ReviewResult(
        corrected={
            node_id: NodeNaming(label=item["label"], one_liner=item["one_liner"])
            for node_id, item in value["corrected"].items()
        },
        page_title=value["page_title"],
        lane_titles=value["lane_titles"],
        findings=[
            ReviewFinding(node_id=item["node_id"], issue=item["issue"])
            for item in value["findings"]
        ],
    )


class ReviewCache(JsonCache[ReviewResult]):
    def __init__(self, path: Path) -> None:
        super().__init__(path, _serialize, _deserialize)
