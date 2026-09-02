from tracer.models.sites import FlowEntry
from tracer.services.analysis.condense.graph_accumulator import GraphAccumulator
from tracer.services.analysis.indexing.service_root_resolver import ServiceRootResolver
from tracer.services.analysis.resolve.call_ancestry_resolver import CallAncestryResolver
from tracer.services.analysis.resolve.indexes import ComponentIndex
from tracer.services.analysis.routes.label_synthesizer import LabelSynthesizer


def entry_fqns(entries: tuple[FlowEntry, ...]) -> dict[str, str]:
    index: dict[str, str] = {}
    for entry in entries:
        for fqn in entry.members or (entry.handler_fqn,):
            index[fqn] = entry.id
    return index


class AnchorResolver:
    def __init__(
        self,
        roots: ServiceRootResolver,
        labels: LabelSynthesizer,
        ancestry: CallAncestryResolver,
        components: ComponentIndex,
    ) -> None:
        self._roots = roots
        self._labels = labels
        self._ancestry = ancestry
        self._components = components

    def attach(
        self,
        acc: GraphAccumulator,
        owner: str,
        head: str,
        entry_fqns: dict[str, str],
        anchors: dict[str, FlowEntry],
    ) -> None:
        parent = self._nearest_ancestor(acc, owner, entry_fqns)
        if parent is not None:
            acc.connect(parent, head, "sequence")
            acc.add_container(head, parent)
            return
        sibling = self._component_host(acc, owner, head)
        if sibling is not None:
            acc.connect(sibling, head, "sequence")
            acc.add_container(head, sibling)
            return
        entry = self._anchor_for(owner, anchors)
        acc.upsert(entry.id, "entry", entry.service_root, entry.label)
        acc.connect(entry.id, head, "sequence")
        acc.add_container(head, entry.id)

    def _nearest_ancestor(
        self, acc: GraphAccumulator, owner: str, entry_fqns: dict[str, str]
    ) -> str | None:
        in_graph = dict(entry_fqns)
        in_graph.update(acc.backing_index())
        return self._ancestry.nearest_ancestor(owner, in_graph)

    def _component_host(self, acc: GraphAccumulator, owner: str, head: str) -> str | None:
        component = self._components.component_of(owner)
        if component is None:
            return None
        drafts = acc.nodes()
        for node_id in sorted(drafts):
            if node_id == head or drafts[node_id].owner_fqn == owner:
                continue
            for fqn in drafts[node_id].backing:
                if self._components.component_of(fqn) == component:
                    return node_id
        return None

    def _anchor_for(self, owner: str, anchors: dict[str, FlowEntry]) -> FlowEntry:
        root = self._roots.root_of(owner)
        component = self._components.component_of(owner) or root
        anchor_id = f"entry:seed:{component}"
        entry = anchors.get(anchor_id)
        if entry is None:
            entry = FlowEntry(
                id=anchor_id,
                handler_fqn=owner,
                label=self._labels.humanize(component),
                service_root=root,
            )
            anchors[anchor_id] = entry
        return entry
