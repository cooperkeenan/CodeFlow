from services.analysis.budget_work_graph import BudgetWorkGraph
from services.analysis.label_synthesizer import LabelSynthesizer


class BudgetRecondenser:
    def __init__(self, labels: LabelSynthesizer) -> None:
        self._labels = labels

    def recondense(self, graph: BudgetWorkGraph) -> None:
        while self._pass(graph):
            continue

    def _pass(self, graph: BudgetWorkGraph) -> bool:
        for key in sorted(graph.edges):
            edge = graph.edges[key]
            if edge.kind != "sequence" or edge.arm_label:
                continue
            head = graph.nodes.get(edge.source)
            tail = graph.nodes.get(edge.target)
            if head is None or tail is None or head.kind != "step" or tail.kind != "step":
                continue
            if len(graph.out_edges(edge.source)) != 1 or len(graph.in_edges(edge.target)) != 1:
                continue
            self._absorb(graph, edge.source, edge.target)
            return True
        return False

    def _absorb(self, graph: BudgetWorkGraph, source: str, target: str) -> None:
        head = graph.nodes[source]
        tail = graph.nodes[target]
        for fqn in tail.backing:
            if fqn not in head.backing:
                head.backing.append(fqn)
        head.refs.extend(tail.refs)
        head.badges = sorted(set(head.badges) | set(tail.badges))
        head.folded_count += tail.folded_count
        for edge in graph.out_edges(target):
            graph.add_edge(source, edge.target, edge.kind, edge.arm_label)
        self._repoint_containers(graph, source, target)
        graph.remove_node(target)
        if head.backing:
            head.label = self._labels.step_label(head.backing)

    def _repoint_containers(self, graph: BudgetWorkGraph, source: str, target: str) -> None:
        for node_id in sorted(graph.nodes):
            if node_id == target:
                continue
            node = graph.nodes[node_id]
            if target in node.containers:
                node.containers.remove(target)
                if (
                    source != node_id
                    and source not in node.containers
                    and not self._is_descendant(graph, source, node_id)
                ):
                    node.containers.append(source)
                node.containers.sort()

    def _is_descendant(self, graph: BudgetWorkGraph, node_id: str, ancestor: str) -> bool:
        seen = {node_id}
        frontier = list(graph.nodes[node_id].containers) if node_id in graph.nodes else []
        while frontier:
            next_frontier: list[str] = []
            for candidate in frontier:
                if candidate == ancestor:
                    return True
                if candidate in seen or candidate not in graph.nodes:
                    continue
                seen.add(candidate)
                next_frontier.extend(graph.nodes[candidate].containers)
            frontier = next_frontier
        return False
