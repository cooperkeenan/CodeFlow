from tracer.services.analysis.budget.budget_work_graph import BudgetWorkGraph

from shared.models.flow_graph import HappyPath


class HappyPathRemapper:
    def remap(self, graph: BudgetWorkGraph) -> None:
        for node in graph.nodes.values():
            if node.kind != "entry":
                continue
            for member in node.members:
                if member.happy is not None:
                    member.happy = self._remap(graph, member.happy)

    def _remap(self, graph: BudgetWorkGraph, happy: HappyPath) -> HappyPath:
        return happy.model_copy(
            update={
                "node_ids": self._resolved(graph, happy.node_ids),
                "hops": self._resolved(graph, happy.hops),
            }
        )

    def _resolved(self, graph: BudgetWorkGraph, ids: list[str]) -> list[str]:
        out: list[str] = []
        for node_id in ids:
            final = graph.resolve(node_id)
            assert final in graph.nodes, f"happy path node {node_id} -> {final} missing"
            if not out or out[-1] != final:
                out.append(final)
        return out
