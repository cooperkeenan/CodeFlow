from models.flow_entry import FlowEntry
from services.analysis.graph_accumulator import GraphAccumulator, _NodeDraft
from services.analysis.label_synthesizer import LabelSynthesizer

_INTERESTING_KINDS = {"decision", "parallel"}
_NOISE_EFFECT = "response"


class TrivialEntryFolder:
    def __init__(self, labels: LabelSynthesizer) -> None:
        self._labels = labels

    def fold(
        self, acc: GraphAccumulator, entries: tuple[FlowEntry, ...]
    ) -> tuple[FlowEntry, ...]:
        adjacency = self._adjacency(acc)
        trivial_ids = {e.id for e in entries if self._is_trivial(acc, adjacency, e.id)}
        if len(trivial_ids) < 2:
            return entries
        trivial = [e for e in entries if e.id in trivial_ids]
        result = [e for e in entries if e.id not in trivial_ids]
        by_root: dict[str, list[FlowEntry]] = {}
        for entry in trivial:
            by_root.setdefault(entry.service_root, []).append(entry)
        for root, members in sorted(by_root.items()):
            if len(members) < 2:
                result.extend(members)
                continue
            result.append(self._fold_group(acc, root, members))
        self._prune_orphans(acc, adjacency, result)
        return tuple(sorted(result, key=lambda e: e.id))

    def _adjacency(self, acc: GraphAccumulator) -> dict[str, list[str]]:
        adjacency: dict[str, list[str]] = {}
        for edge in acc.edges().values():
            adjacency.setdefault(edge.source, []).append(edge.target)
        return adjacency

    def _is_trivial(
        self, acc: GraphAccumulator, adjacency: dict[str, list[str]], entry_id: str
    ) -> bool:
        nodes = acc.nodes()
        seen: set[str] = set()
        stack = [entry_id]
        while stack:
            current = stack.pop()
            if current in seen:
                continue
            seen.add(current)
            node = nodes.get(current)
            if current != entry_id and node is not None and self._is_interesting(node):
                return False
            stack.extend(adjacency.get(current, ()))
        return True

    def _is_interesting(self, node: _NodeDraft) -> bool:
        if node.kind in _INTERESTING_KINDS:
            return True
        return node.kind == "effect" and node.effect_kind != _NOISE_EFFECT

    def _fold_group(
        self, acc: GraphAccumulator, root: str, members: list[FlowEntry]
    ) -> FlowEntry:
        for entry in members:
            acc.remove_node(entry.id)
        total_routes = sum(entry.route_count for entry in members)
        label = f"{self._labels.humanize(root)} · {total_routes} routes, no logic"
        grouped = FlowEntry(
            id=f"entry:trivial:{root}",
            handler_fqn=members[0].handler_fqn,
            label=label,
            service_root=root,
            members=tuple(m.handler_fqn for m in members),
            route_count=total_routes,
        )
        acc.upsert(grouped.id, "entry", root, grouped.label, folded_count=total_routes)
        return grouped

    def _prune_orphans(
        self, acc: GraphAccumulator, adjacency: dict[str, list[str]], entries: list[FlowEntry]
    ) -> None:
        seen: set[str] = set()
        stack = [entry.id for entry in entries]
        while stack:
            current = stack.pop()
            if current in seen:
                continue
            seen.add(current)
            stack.extend(adjacency.get(current, ()))
        for node_id in [nid for nid in acc.nodes() if nid not in seen]:
            acc.remove_node(node_id)
