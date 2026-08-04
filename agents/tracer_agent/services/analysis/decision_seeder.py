from models.flow_entry import FlowEntry
from models.project_index import ProjectIndex
from models.significance_result import SignificanceResult
from services.analysis.anchor_resolver import AnchorResolver, entry_fqns
from services.analysis.function_summarizer import FunctionSummarizer
from services.analysis.graph_accumulator import GraphAccumulator


class DecisionSeeder:
    def __init__(self, index: ProjectIndex, anchor: AnchorResolver) -> None:
        self._index = index
        self._anchor = anchor

    def seed(
        self,
        acc: GraphAccumulator,
        summarizer: FunctionSummarizer,
        significance: SignificanceResult,
        entries: tuple[FlowEntry, ...],
    ) -> tuple[FlowEntry, ...]:
        anchors: dict[str, FlowEntry] = {}
        fqns = entry_fqns(entries)
        for site_id in sorted(significance.verdicts):
            verdict = significance.verdicts[site_id]
            if verdict.verdict != "decision":
                continue
            if f"dec:{site_id}" in acc.nodes():
                continue
            self._seed_one(acc, summarizer, site_id, anchors, fqns)
        return tuple(sorted(anchors.values(), key=lambda entry: entry.id))

    def _seed_one(
        self,
        acc: GraphAccumulator,
        summarizer: FunctionSummarizer,
        site_id: str,
        anchors: dict[str, FlowEntry],
        entry_fqns: dict[str, str],
    ) -> None:
        owner = site_id.rsplit(":", 1)[0]
        if owner not in self._index.functions:
            return
        summary = summarizer.summarize(owner)
        if summary.head is None:
            return
        self._anchor.attach(acc, owner, summary.head, entry_fqns, anchors)
