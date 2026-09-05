from shared.flow_endpoints.back_edge_pruner import BackEdgePruner
from shared.flow_endpoints.chunk_dissolver import ChunkDissolver
from shared.flow_endpoints.endpoint_elider import EndpointElider
from shared.flow_endpoints.level_assigner import LevelAssigner
from shared.flow_endpoints.shared_owner_index import SharedOwnerIndex
from shared.flow_endpoints.terminal_closer import TerminalCloser
from shared.flow_endpoints.slice_graph import SliceGraph
from shared.models.flow_graph import FlowEdge, FlowGraph, FlowNode, Lane

ENDPOINT_LANE_ID = "endpoint"


class EndpointSubgraph:
    def __init__(
        self,
        pruner: BackEdgePruner | None = None,
        elider: EndpointElider | None = None,
        owners: SharedOwnerIndex | None = None,
    ) -> None:
        self._pruner = pruner or BackEdgePruner()
        self._elider = elider or EndpointElider(ChunkDissolver(), LevelAssigner())
        self._owners = owners or SharedOwnerIndex()

    def slice(self, graph: FlowGraph, entry_id: str) -> FlowGraph | None:
        nodes_by_id = {node.id: node for node in graph.nodes}
        root = nodes_by_id.get(entry_id)
        if root is None or root.kind != "entry":
            return None
        member_ids = self._closure(entry_id, nodes_by_id)
        working = SliceGraph(
            {node_id: self._scoped(nodes_by_id[node_id], member_ids) for node_id in member_ids},
            self._edges(graph.edges, member_ids, entry_id),
            entry_id,
            self._external(graph, member_ids),
        )
        self._elider.elide(
            working,
            self._owners.counts(graph),
            TerminalCloser(nodes_by_id, self._entry_ids(graph)),
        )
        title = root.llm_label or root.label
        return FlowGraph(
            repo=graph.repo,
            page_title=title,
            lanes=[
                Lane(
                    id=ENDPOINT_LANE_ID,
                    name=title,
                    entry_ids=[entry_id],
                    mass=float(len(working.nodes)),
                )
            ],
            nodes=[working.nodes[node_id] for node_id in sorted(working.nodes)],
            edges=working.edges,
            meta={"entry_id": entry_id, "entry_label": root.label},
        )

    def _edges(
        self, edges: list[FlowEdge], member_ids: set[str], entry_id: str
    ) -> list[FlowEdge]:
        inside = [
            edge.model_copy(deep=True)
            for edge in edges
            if edge.source in member_ids and edge.target in member_ids
        ]
        return self._pruner.prune(member_ids, inside, entry_id)

    def _external(self, graph: FlowGraph, member_ids: set[str]) -> dict[str, list[str]]:
        outside: dict[str, list[str]] = {}
        for edge in graph.edges:
            if edge.source in member_ids and edge.target not in member_ids:
                outside.setdefault(edge.source, []).append(edge.target)
        return {source: sorted(targets) for source, targets in outside.items()}

    def _entry_ids(self, graph: FlowGraph) -> frozenset[str]:
        return frozenset(
            node.id for node in graph.nodes if node.kind == "entry" and node.id.startswith("entry:")
        )

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

    def _scoped(self, node: FlowNode, member_ids: set[str]) -> FlowNode:
        return node.model_copy(
            deep=True,
            update={
                "lane": ENDPOINT_LANE_ID,
                "level": 0,
                "hidden_children": [],
                "containers": [c for c in node.containers if c in member_ids],
                "body_head": "",
                "body_tails": [],
            },
        )
