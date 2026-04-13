import logging
import shutil

import networkx as nx

logger = logging.getLogger(__name__)


class CallGraphService:
    def build(self, temp_dir: str, entry_files: list[str]) -> dict:
        logger.info("Running pycg on %d files in %s", len(entry_files), temp_dir)
        try:
            from pycg import CallGraphGenerator

            cg = CallGraphGenerator(entry_files, temp_dir)
            cg.analyze()
            raw = cg.output()

            graph = self._to_networkx(raw)
            result = self._to_serialisable(graph)

            logger.info(
                "Call graph built: %d nodes, %d edges",
                graph.number_of_nodes(),
                graph.number_of_edges(),
            )
            return result
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)
            logger.info("Cleaned up temp dir %s", temp_dir)

    def _to_networkx(self, pycg_output: dict) -> nx.DiGraph:
        graph = nx.DiGraph()
        for caller, callees in pycg_output.items():
            if caller not in graph:
                graph.add_node(caller)
            for callee in callees:
                graph.add_edge(caller, callee)
        return graph

    def _to_serialisable(self, graph: nx.DiGraph) -> dict:
        return {
            "nodes": list(graph.nodes()),
            "edges": [
                {"from": u, "to": v}
                for u, v in graph.edges()
            ],
        }
