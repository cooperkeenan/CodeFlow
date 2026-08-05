from models.flow_entry import FlowEntry
from services.analysis.anchor_resolver import AnchorResolver, entry_fqns
from services.analysis.graph_accumulator import GraphAccumulator
from services.analysis.graph_drafts import _NodeDraft


class IslandAnchor:
    def __init__(self, anchor: AnchorResolver) -> None:
        self._anchor = anchor

    def anchor(
        self, acc: GraphAccumulator, entries: tuple[FlowEntry, ...]
    ) -> tuple[FlowEntry, ...]:
        anchors: dict[str, FlowEntry] = {}
        fqns = entry_fqns(entries)
        reachable = self._reachable(acc)
        stranded = set(acc.nodes()) - reachable
        for component in self._components(acc, stranded):
            head = self._head(acc, component)
            owner = acc.nodes()[head].owner_fqn
            self._anchor.attach(acc, owner, head, fqns, anchors)
        return tuple(sorted(anchors.values(), key=lambda entry: entry.id))

    def _reachable(self, acc: GraphAccumulator) -> set[str]:
        nodes = acc.nodes()
        adj: dict[str, list[str]] = {}
        for edge in acc.edges().values():
            adj.setdefault(edge.source, []).append(edge.target)
        seen: set[str] = set()
        stack = sorted(nid for nid, draft in nodes.items() if draft.kind == "entry")
        while stack:
            node_id = stack.pop()
            if node_id in seen:
                continue
            seen.add(node_id)
            stack.extend(adj.get(node_id, ()))
        return seen

    def _components(
        self, acc: GraphAccumulator, stranded: set[str]
    ) -> list[list[str]]:
        adj: dict[str, set[str]] = {node_id: set() for node_id in stranded}
        for edge in acc.edges().values():
            if edge.source in stranded and edge.target in stranded:
                adj[edge.source].add(edge.target)
                adj[edge.target].add(edge.source)
        seen: set[str] = set()
        groups: list[list[str]] = []
        for start in sorted(stranded):
            if start in seen:
                continue
            stack = [start]
            members: set[str] = set()
            while stack:
                node_id = stack.pop()
                if node_id in members:
                    continue
                members.add(node_id)
                stack.extend(sorted(adj.get(node_id, ())))
            seen |= members
            groups.append(sorted(members))
        return sorted(groups)

    def _head(self, acc: GraphAccumulator, component: list[str]) -> str:
        nodes = acc.nodes()
        members = set(component)
        has_internal_in: set[str] = set()
        for edge in acc.edges().values():
            if edge.source in members and edge.target in members:
                has_internal_in.add(edge.target)
        candidates = [node_id for node_id in component if node_id not in has_internal_in]
        pool = candidates or component
        return min(pool, key=lambda node_id: self._sort_key(nodes, node_id))

    def _sort_key(self, nodes: dict[str, _NodeDraft], node_id: str) -> tuple[str, int, str]:
        refs = nodes[node_id].refs
        if refs:
            return (refs[0].file, refs[0].line, node_id)
        return ("", 0, node_id)
