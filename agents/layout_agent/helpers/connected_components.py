from collections import deque

from helpers.module_graph import ModuleGraphBuilder
from shared.models.diagram_spec import DiagramSpec


class ConnectedComponents:
    def __init__(self, graph_builder: ModuleGraphBuilder) -> None:
        self._graph_builder = graph_builder

    def largest(self, spec: DiagramSpec) -> set[str]:
        graph = self._graph_builder.build(spec)
        names = graph.module_names
        if not names:
            return set()
        if len(names) == 1:
            return {names[0]}

        undirected: dict[str, set[str]] = {n: set() for n in names}
        for src, targets in graph.adjacency.items():
            for tgt in targets:
                undirected[src].add(tgt)
                undirected[tgt].add(src)

        visited: set[str] = set()
        components: list[set[str]] = []

        for start in sorted(names):
            if start in visited:
                continue
            component: set[str] = set()
            queue: deque[str] = deque([start])
            while queue:
                node = queue.popleft()
                if node in visited:
                    continue
                visited.add(node)
                component.add(node)
                for neighbour in undirected.get(node, set()):
                    if neighbour not in visited:
                        queue.append(neighbour)
            components.append(component)

        components.sort(key=lambda c: (-len(c), min(c)))
        return components[0]
