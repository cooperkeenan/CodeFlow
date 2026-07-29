from models.flow_entry import FlowEntry
from models.project_index import ProjectIndex
from models.significance_result import SignificanceResult
from services.analysis.function_summarizer import FunctionSummarizer
from services.analysis.graph_accumulator import GraphAccumulator
from services.analysis.label_synthesizer import LabelSynthesizer
from services.analysis.service_root_resolver import ServiceRootResolver


class DecisionSeeder:
    def __init__(
        self, index: ProjectIndex, roots: ServiceRootResolver, labels: LabelSynthesizer
    ) -> None:
        self._index = index
        self._roots = roots
        self._labels = labels

    def seed(
        self,
        acc: GraphAccumulator,
        summarizer: FunctionSummarizer,
        significance: SignificanceResult,
    ) -> tuple[FlowEntry, ...]:
        anchors: dict[str, FlowEntry] = {}
        for site_id in sorted(significance.verdicts):
            verdict = significance.verdicts[site_id]
            if verdict.verdict != "decision":
                continue
            if f"dec:{site_id}" in acc.nodes():
                continue
            self._seed_one(acc, summarizer, site_id, anchors)
        return tuple(sorted(anchors.values(), key=lambda entry: entry.id))

    def _seed_one(
        self,
        acc: GraphAccumulator,
        summarizer: FunctionSummarizer,
        site_id: str,
        anchors: dict[str, FlowEntry],
    ) -> None:
        owner = site_id.rsplit(":", 1)[0]
        if owner not in self._index.functions:
            return
        summary = summarizer.summarize(owner)
        if summary.head is None:
            return
        entry = self._anchor_for(owner, anchors)
        acc.upsert(entry.id, "entry", entry.service_root, entry.label)
        acc.connect(entry.id, summary.head, "sequence")

    def _anchor_for(self, owner: str, anchors: dict[str, FlowEntry]) -> FlowEntry:
        root = self._roots.root_of(owner)
        anchor_id = f"entry:seed:{root}"
        entry = anchors.get(anchor_id)
        if entry is None:
            entry = FlowEntry(
                id=anchor_id,
                handler_fqn=owner,
                label=f"{self._labels.humanize(root)} · other decisions",
                service_root=root,
            )
            anchors[anchor_id] = entry
        return entry
