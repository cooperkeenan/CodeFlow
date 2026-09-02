from tracer.models.pillar_scores import PillarScores
from tracer.services.analysis.budget.budget_work_graph import BudgetWorkGraph
from tracer.services.analysis.resolve.indexes import ComponentIndex

from shared.models.flow_graph import FlowNode

_SEED_PREFIX = "entry:seed:"


class PillarGatewaySelector:
    def component_of(self, node: FlowNode, components: ComponentIndex) -> str | None:
        if node.id.startswith(_SEED_PREFIX):
            return node.id[len(_SEED_PREFIX) :]
        for fqn in node.backing:
            component = components.component_of(fqn)
            if component is not None:
                return component
        return None

    def select(
        self, graph: BudgetWorkGraph, pillars: PillarScores, components: ComponentIndex
    ) -> frozenset[str]:
        grouped: dict[str, list[FlowNode]] = {}
        for node_id in sorted(graph.nodes):
            node = graph.nodes[node_id]
            if node.level != 0:
                continue
            component = self.component_of(node, components)
            if component is None or pillars.score(component) <= 0.0:
                continue
            grouped.setdefault(component, []).append(node)
        gateways: set[str] = set()
        for component in sorted(grouped):
            best = min(grouped[component], key=lambda node: self._rank(graph, node))
            gateways.add(best.id)
        return frozenset(gateways)

    def _rank(self, graph: BudgetWorkGraph, node: FlowNode) -> tuple[int, int, int, str]:
        entry_first = 0 if node.kind == "entry" else 1
        predecessors = len({edge.source for edge in graph.in_edges(node.id)})
        return (entry_first, -predecessors, -len(graph.out_edges(node.id)), node.id)
