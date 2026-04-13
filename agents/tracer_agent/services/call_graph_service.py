# agents/tracer_agent/services/call_graph_service.py
import logging
import shutil

import networkx as nx
from pyan.analyzer import CallGraphVisitor

logger = logging.getLogger(__name__)


class CallGraphService:
    def build(self, temp_dir: str, entry_files: list[str]) -> dict:
        logger.info("Running pyan3 on %d files in %s", len(entry_files), temp_dir)
        try:
            visitor = CallGraphVisitor(entry_files, root=temp_dir)
            graph = self._to_networkx(visitor)

            logger.info(
                "Call graph built: %d nodes, %d edges",
                graph.number_of_nodes(),
                graph.number_of_edges(),
            )
            return self._to_serialisable(graph)
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)
            logger.info("Cleaned up temp dir %s", temp_dir)

    def _to_networkx(self, visitor: CallGraphVisitor) -> nx.DiGraph:
        graph = nx.DiGraph()
        for node, targets in visitor.uses_edges.items():
            caller = node.get_name()
            graph.add_node(caller)
            for target in targets:
                callee = target.get_name()
                graph.add_edge(caller, callee)
        return graph

    def _to_serialisable(self, graph: nx.DiGraph) -> dict:
        graph.remove_nodes_from(list(nx.isolates(graph)))
        edges = [{"from": u, "to": v} for u, v in graph.edges()][:300]
        nodes = list({n for e in edges for n in (e["from"], e["to"])})
        return {"nodes": nodes, "edges": edges}