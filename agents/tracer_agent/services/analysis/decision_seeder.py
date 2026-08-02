from models.flow_entry import FlowEntry
from models.project_index import ProjectIndex
from models.significance_result import SignificanceResult
from services.analysis.call_ancestry_resolver import CallAncestryResolver
from services.analysis.function_summarizer import FunctionSummarizer
from services.analysis.graph_accumulator import GraphAccumulator
from services.analysis.label_synthesizer import LabelSynthesizer
from services.analysis.service_root_resolver import ServiceRootResolver


class DecisionSeeder:
    def __init__(
        self,
        index: ProjectIndex,
        roots: ServiceRootResolver,
        labels: LabelSynthesizer,
        ancestry: CallAncestryResolver,
    ) -> None:
        self._index = index
        self._roots = roots
        self._labels = labels
        self._ancestry = ancestry

    def seed(
        self,
        acc: GraphAccumulator,
        summarizer: FunctionSummarizer,
        significance: SignificanceResult,
        entries: tuple[FlowEntry, ...],
    ) -> tuple[FlowEntry, ...]:
        anchors: dict[str, FlowEntry] = {}
        entry_fqns = self._entry_fqns(entries)
        for site_id in sorted(significance.verdicts):
            verdict = significance.verdicts[site_id]
            if verdict.verdict != "decision":
                continue
            if f"dec:{site_id}" in acc.nodes():
                continue
            self._seed_one(acc, summarizer, site_id, anchors, entry_fqns)
        return tuple(sorted(anchors.values(), key=lambda entry: entry.id))

    def _entry_fqns(self, entries: tuple[FlowEntry, ...]) -> dict[str, str]:
        index: dict[str, str] = {}
        for entry in entries:
            for fqn in entry.members or (entry.handler_fqn,):
                index[fqn] = entry.id
        return index

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
        parent = self._nearest_ancestor(acc, owner, entry_fqns)
        if parent is not None:
            acc.connect(parent, summary.head, "sequence")
            return
        entry = self._anchor_for(owner, anchors)
        acc.upsert(entry.id, "entry", entry.service_root, entry.label)
        acc.connect(entry.id, summary.head, "sequence")

    def _nearest_ancestor(
        self, acc: GraphAccumulator, owner: str, entry_fqns: dict[str, str]
    ) -> str | None:
        in_graph = dict(entry_fqns)
        in_graph.update(acc.backing_index())
        return self._ancestry.nearest_ancestor(owner, in_graph)

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
