from collections import defaultdict

from services.analysis.budget_work_graph import BudgetWorkGraph
from services.analysis.container_repointer import ContainerRepointer

_MAX_SAME_KIND = 3


class EffectCapper:
    def __init__(self, repointer: ContainerRepointer) -> None:
        self._repointer = repointer

    def cap(self, graph: BudgetWorkGraph) -> None:
        self._dedupe(graph)
        self._collapse_kinds(graph)

    def _dedupe(self, graph: BudgetWorkGraph) -> None:
        groups: dict[tuple[str, str, str], list[str]] = defaultdict(list)
        for node in graph.nodes.values():
            if node.kind == "effect":
                groups[(node.lane, node.effect_kind or "", node.effect_target)].append(node.id)
        for ids in groups.values():
            self._merge(graph, sorted(ids), fold=False)

    def _collapse_kinds(self, graph: BudgetWorkGraph) -> None:
        groups: dict[tuple[str, str], list[str]] = defaultdict(list)
        for node in graph.nodes.values():
            if node.kind == "effect":
                groups[(node.lane, node.effect_kind or "")].append(node.id)
        for ids in groups.values():
            if len(ids) > _MAX_SAME_KIND:
                self._merge(graph, sorted(ids), fold=True)

    def _merge(self, graph: BudgetWorkGraph, ids: list[str], fold: bool) -> None:
        if len(ids) < 2:
            return
        keep = ids[0]
        keeper = graph.nodes[keep]
        for other in ids[1:]:
            keeper.folded_count += graph.nodes[other].folded_count + 1
            for edge in graph.in_edges(other):
                graph.add_edge(edge.source, keep, edge.kind, edge.arm_label)
            for edge in graph.out_edges(other):
                graph.add_edge(keep, edge.target, edge.kind, edge.arm_label)
            self._repointer.repoint(graph.nodes, keep, other)
            graph.remove_node(other)
        if fold:
            keeper.badges = sorted(set(keeper.badges) | {"folded"})
