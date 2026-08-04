import json
from pathlib import Path

from models.node_naming import NodeNaming
from models.review_finding import ReviewFinding
from models.review_result import ReviewResult


class ReviewCache:
    def __init__(self, path: Path) -> None:
        self._path = path
        self._entries: dict[str, ReviewResult] = self._load()

    def get(self, fingerprint: str) -> ReviewResult | None:
        return self._entries.get(fingerprint)

    def put(self, fingerprint: str, result: ReviewResult) -> None:
        self._entries[fingerprint] = result

    def flush(self) -> None:
        self._path.parent.mkdir(parents=True, exist_ok=True)
        payload = {key: self._serialize(value) for key, value in self._entries.items()}
        self._path.write_text(json.dumps(payload, indent=2, sort_keys=True))

    def _load(self) -> dict[str, ReviewResult]:
        if not self._path.exists():
            return {}
        try:
            raw = json.loads(self._path.read_text())
        except (OSError, json.JSONDecodeError):
            return {}
        entries: dict[str, ReviewResult] = {}
        for key, value in raw.items():
            try:
                entries[key] = self._deserialize(value)
            except (KeyError, TypeError, ValueError):
                continue
        return entries

    def _serialize(self, result: ReviewResult) -> dict:
        return {
            "corrected": {
                node_id: {"label": naming.label, "one_liner": naming.one_liner}
                for node_id, naming in result.corrected.items()
            },
            "page_title": result.page_title,
            "lane_titles": result.lane_titles,
            "findings": [{"node_id": f.node_id, "issue": f.issue} for f in result.findings],
        }

    def _deserialize(self, value: dict) -> ReviewResult:
        corrected = {
            node_id: NodeNaming(label=item["label"], one_liner=item["one_liner"])
            for node_id, item in value["corrected"].items()
        }
        findings = [
            ReviewFinding(node_id=item["node_id"], issue=item["issue"])
            for item in value["findings"]
        ]
        return ReviewResult(
            corrected=corrected,
            page_title=value["page_title"],
            lane_titles=value["lane_titles"],
            findings=findings,
        )
