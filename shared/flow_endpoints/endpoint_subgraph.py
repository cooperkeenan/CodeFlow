from shared.flow_endpoints.chunk_dissolver import ChunkDissolver
from shared.flow_endpoints.endpoint_elider import EndpointElider
from shared.flow_endpoints.level_assigner import LevelAssigner
from shared.flow_endpoints.shared_owner_index import SharedOwnerIndex
from shared.flow_endpoints.slice_assembler import SliceAssembler
from shared.models.flow_graph import FlowGraph, FlowNode


class EndpointSubgraph:
    def __init__(
        self,
        assembler: SliceAssembler | None = None,
        elider: EndpointElider | None = None,
        owners: SharedOwnerIndex | None = None,
    ) -> None:
        self._assembler = assembler or SliceAssembler()
        self._elider = elider or EndpointElider(ChunkDissolver(), LevelAssigner())
        self._owners = owners or SharedOwnerIndex()

    def slice(self, graph: FlowGraph, entry_id: str) -> FlowGraph | None:
        nodes_by_id = {node.id: node for node in graph.nodes}
        root = nodes_by_id.get(entry_id)
        if root is None or root.kind != "entry":
            return None
        return self.slice_root(graph, entry_id)

    def slice_root(self, graph: FlowGraph, root_id: str) -> FlowGraph | None:
        nodes_by_id = {node.id: node for node in graph.nodes}
        root = nodes_by_id.get(root_id)
        if root is None:
            return None
        member_ids = self._closure(root_id, nodes_by_id)
        working = self._assembler.working(graph, nodes_by_id, member_ids, root_id)
        self._elider.elide(
            working,
            self._owners.counts(graph),
            self._assembler.closer(graph, nodes_by_id),
        )
        meta = {"entry_id": root_id, "entry_label": root.label}
        return self._assembler.finish(graph, working, root, meta)

    def _closure(self, entry_id: str, nodes_by_id: dict[str, FlowNode]) -> set[str]:
        seen = {entry_id}
        stack = [entry_id]
        while stack:
            current = stack.pop()
            for child_id in nodes_by_id[current].hidden_children:
                if child_id in nodes_by_id and child_id not in seen:
                    seen.add(child_id)
                    stack.append(child_id)
        return seen
