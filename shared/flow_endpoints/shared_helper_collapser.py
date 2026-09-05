from shared.flow_endpoints.slice_graph import SliceGraph
from shared.models.flow_graph import FlowNode

HELPER_PREFIX = "helper:"
_MIN_SHARED_ENDPOINTS = 10


class SharedHelperCollapser:
    def __init__(self, min_shared: int = _MIN_SHARED_ENDPOINTS, floor: int = 10) -> None:
        self._min_shared = min_shared
        self._floor = floor

    def collapse(self, graph: SliceGraph, exclusivity: dict[str, int]) -> None:
        groups: dict[str, list[str]] = {}
        for node_id in sorted(graph.keep):
            owner = graph.nodes[node_id].owner_fqn
            if not owner or node_id == graph.root_id:
                continue
            if exclusivity.get(owner, 0) < self._min_shared:
                continue
            groups.setdefault(owner, []).append(node_id)
        for owner, members in sorted(groups.items()):
            if len(members) < 2:
                continue
            if len(graph.keep) - len(members) + 1 < self._floor:
                continue
            self._fold(graph, owner, members)

    def _fold(self, graph: SliceGraph, owner: str, members: list[str]) -> None:
        member_set = set(members)
        heads = [
            member
            for member in members
            if not any(p in member_set for p in graph.predecessors(member))
        ]
        source = graph.nodes[heads[0] if heads else members[0]]
        host = FlowNode(
            id=f"{HELPER_PREFIX}{owner}",
            kind="step",
            lane=source.lane,
            label=source.label,
            llm_label=source.llm_label,
            one_liner=source.one_liner,
            refs=list(source.refs[:1]),
            badges=["folded"],
            folded_count=len(members) - 1,
            owner_fqn=owner,
        )
        graph.add_node(host)
        graph.absorb(member_set | {host.id}, host.id)
