import logging
from collections import deque

from helpers.archetype_classifier import ArchetypeClassifier
from helpers.module_graph import ModuleGraph, ModuleGraphBuilder

from shared.models.diagram_spec import (
    Archetype,
    DiagramSpec,
    LayoutHint,
    RankAssignment,
)

logger = logging.getLogger(__name__)


class LayoutService:
    def __init__(self, graph_builder: ModuleGraphBuilder, classifier: ArchetypeClassifier):
        self._graph_builder = graph_builder
        self._classifier = classifier

    def layout(self, spec: DiagramSpec) -> LayoutHint:
        graph = self._graph_builder.build(spec)
        archetype, rationale = self._classifier.classify(graph)
        order = self._order(archetype, graph)
        ranks = self._ranks(archetype, graph, order)
        logger.info("Layout: archetype=%s rationale=%s", archetype, rationale)
        logger.info("  order=%s", order)
        return LayoutHint(
            archetype=archetype,
            module_order=order,
            rank_assignments=[RankAssignment(module_name=n, rank=r) for n, r in ranks.items()],
            rationale=rationale,
        )

    def _order(self, archetype: Archetype, graph: ModuleGraph) -> list[str]:
        if archetype == "pipeline":
            return self._pipeline_order(graph)
        if archetype == "hub":
            return self._hub_order(graph)
        if archetype in ("layered", "hierarchy"):
            return self._bfs_order(graph)
        return sorted(graph.module_names)

    def _ranks(
        self, archetype: Archetype, graph: ModuleGraph, order: list[str]
    ) -> dict[str, int]:
        if archetype == "pipeline":
            return {name: i for i, name in enumerate(order)}
        if archetype == "hub":
            hub = order[0] if order else ""
            return {name: (0 if name == hub else 1) for name in graph.module_names}
        if archetype in ("layered", "hierarchy"):
            return self._bfs_depth(graph)
        return {name: 0 for name in graph.module_names}

    def _pipeline_order(self, graph: ModuleGraph) -> list[str]:
        chain = list(graph.longest_path) or list(graph.topological_order or sorted(graph.module_names))
        chain_set = set(chain)
        extras = sorted(n for n in graph.module_names if n not in chain_set)
        return [*chain, *extras]

    def _hub_order(self, graph: ModuleGraph) -> list[str]:
        if not graph.module_names:
            return []
        def hubness(name: str) -> int:
            return max(graph.fan_out.get(name, 0), graph.fan_in.get(name, 0))
        hub = max(graph.module_names, key=lambda n: (hubness(n), -graph.module_names.index(n)))
        spokes = sorted(n for n in graph.module_names if n != hub)
        return [hub, *spokes]

    def _bfs_order(self, graph: ModuleGraph) -> list[str]:
        depth = self._bfs_depth(graph)
        return sorted(graph.module_names, key=lambda n: (depth.get(n, 0), n))

    def _bfs_depth(self, graph: ModuleGraph) -> dict[str, int]:
        depth: dict[str, int] = {}
        seeds = graph.entry_modules or self._roots(graph)
        queue: deque[tuple[str, int]] = deque((s, 0) for s in seeds)
        seen: set[str] = set(seeds)
        while queue:
            node, level = queue.popleft()
            depth[node] = level
            for nxt in sorted(graph.adjacency.get(node, set())):
                if nxt not in seen:
                    seen.add(nxt)
                    queue.append((nxt, level + 1))
        for name in graph.module_names:
            depth.setdefault(name, 0)
        return depth

    def _roots(self, graph: ModuleGraph) -> list[str]:
        roots = [n for n in graph.module_names if not graph.reverse_adjacency.get(n)]
        return roots or list(graph.module_names[:1])
