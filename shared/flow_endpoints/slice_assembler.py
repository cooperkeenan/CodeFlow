from itertools import pairwise

from shared.flow_endpoints.back_edge_pruner import BackEdgePruner
from shared.flow_endpoints.slice_graph import SliceGraph
from shared.flow_endpoints.terminal_closer import TerminalCloser
from shared.models.flow_graph import FlowEdge, FlowGraph, FlowNode, Lane

ENDPOINT_LANE_ID = "endpoint"


class SliceAssembler:
    def __init__(self, pruner: BackEdgePruner | None = None) -> None:
        self._pruner = pruner or BackEdgePruner()

    def working(
        self,
        graph: FlowGraph,
        nodes_by_id: dict[str, FlowNode],
        member_ids: set[str],
        root_id: str,
        pairs: set[tuple[str, str]] | None = None,
    ) -> SliceGraph:
        return SliceGraph(
            {node_id: self._scoped(nodes_by_id[node_id], member_ids) for node_id in member_ids},
            self._edges(graph.edges, member_ids, root_id, pairs),
            root_id,
            self._external(graph, member_ids),
        )

    def working_for_path(
        self,
        graph: FlowGraph,
        nodes_by_id: dict[str, FlowNode],
        member_ids: set[str],
        root_id: str,
        path: list[str],
    ) -> SliceGraph:
        return self.working(graph, nodes_by_id, member_ids, root_id, set(pairwise(path)))

    def closer(self, graph: FlowGraph, nodes_by_id: dict[str, FlowNode]) -> TerminalCloser:
        return TerminalCloser(nodes_by_id, self._entry_ids(graph))

    def finish(self, graph: FlowGraph, working: SliceGraph, root: FlowNode, meta: dict) -> FlowGraph:
        title = root.llm_label or root.label
        return FlowGraph(
            repo=graph.repo,
            page_title=title,
            lanes=[
                Lane(
                    id=ENDPOINT_LANE_ID,
                    name=title,
                    entry_ids=[root.id],
                    mass=float(len(working.nodes)),
                )
            ],
            nodes=[working.nodes[node_id] for node_id in sorted(working.nodes)],
            edges=working.edges,
            meta=meta,
        )

    def _edges(
        self,
        edges: list[FlowEdge],
        member_ids: set[str],
        root_id: str,
        pairs: set[tuple[str, str]] | None,
    ) -> list[FlowEdge]:
        inside = [
            edge.model_copy(deep=True)
            for edge in edges
            if edge.source in member_ids and edge.target in member_ids
        ]
        return self._pruner.prune(member_ids, inside, root_id, pairs)

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
