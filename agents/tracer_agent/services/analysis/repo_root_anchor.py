from services.analysis.budget_work_graph import BudgetWorkGraph
from shared.models.flow_graph import FlowNode


class RepoRootAnchor:
    def anchor(self, graph: BudgetWorkGraph) -> None:
        root_id = f"root:{graph.repo}"
        graph.nodes[root_id] = FlowNode(id=root_id, kind="entry", lane=root_id, label=graph.repo)
        for node_id in sorted(graph.nodes):
            if node_id == root_id:
                continue
            if not graph.nodes[node_id].containers:
                graph.nodes[node_id].containers = [root_id]
