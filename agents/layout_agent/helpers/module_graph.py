from collections import defaultdict, deque
from dataclasses import dataclass

from shared.models.diagram_spec import DiagramSpec


@dataclass(frozen=True)
class ModuleGraph:
    module_names: list[str]
    adjacency: dict[str, set[str]]
    reverse_adjacency: dict[str, set[str]]
    cycles: int
    longest_path: list[str]
    topological_order: list[str]
    fan_out: dict[str, int]
    fan_in: dict[str, int]
    zone_uniformity: float
    entry_modules: list[str]
    zones_by_module: dict[str, set[str]]


class ModuleGraphBuilder:
    def build(self, spec: DiagramSpec) -> ModuleGraph:
        names = [m.name for m in spec.modules]
        comp_to_mod = self._comp_to_module(spec)
        zones_by_module = {m.name: set(m.zones.keys()) for m in spec.modules}
        adjacency = self._adjacency(spec, comp_to_mod, set(names))
        reverse = self._reverse(adjacency, names)
        cycles = self._count_cycles(names, adjacency)
        topo = self._topological(names, adjacency) if cycles == 0 else []
        longest = self._longest_path(topo, adjacency) if topo else []
        fan_out = {n: len(adjacency.get(n, set())) for n in names}
        fan_in = {n: len(reverse.get(n, set())) for n in names}
        uniformity = self._zone_uniformity(zones_by_module)
        entry_modules = self._entry_modules(spec, comp_to_mod)
        return ModuleGraph(
            module_names=names,
            adjacency=adjacency,
            reverse_adjacency=reverse,
            cycles=cycles,
            longest_path=longest,
            topological_order=topo,
            fan_out=fan_out,
            fan_in=fan_in,
            zone_uniformity=uniformity,
            entry_modules=entry_modules,
            zones_by_module=zones_by_module,
        )

    def _comp_to_module(self, spec: DiagramSpec) -> dict[str, str]:
        result: dict[str, str] = {}
        for module in spec.modules:
            for components in module.zones.values():
                for component in components:
                    result[component.name] = module.name
        return result

    def _adjacency(
        self, spec: DiagramSpec, comp_to_mod: dict[str, str], valid: set[str]
    ) -> dict[str, set[str]]:
        adj: dict[str, set[str]] = defaultdict(set)
        for edge in spec.edges:
            src_mod = comp_to_mod.get(edge.source)
            tgt_mod = comp_to_mod.get(edge.target)
            if src_mod is None or tgt_mod is None or src_mod == tgt_mod:
                continue
            if src_mod in valid and tgt_mod in valid:
                adj[src_mod].add(tgt_mod)
        return dict(adj)

    def _reverse(self, adj: dict[str, set[str]], names: list[str]) -> dict[str, set[str]]:
        rev: dict[str, set[str]] = {n: set() for n in names}
        for src, targets in adj.items():
            for tgt in targets:
                rev[tgt].add(src)
        return rev

    def _count_cycles(self, names: list[str], adj: dict[str, set[str]]) -> int:
        WHITE, GREY, BLACK = 0, 1, 2
        colour = {n: WHITE for n in names}
        count = 0

        def visit(node: str) -> None:
            nonlocal count
            colour[node] = GREY
            for nxt in adj.get(node, set()):
                if colour[nxt] == GREY:
                    count += 1
                elif colour[nxt] == WHITE:
                    visit(nxt)
            colour[node] = BLACK

        for n in names:
            if colour[n] == WHITE:
                visit(n)
        return count

    def _topological(self, names: list[str], adj: dict[str, set[str]]) -> list[str]:
        indegree = {n: 0 for n in names}
        for src in names:
            for tgt in adj.get(src, set()):
                indegree[tgt] += 1
        queue = deque(sorted(n for n in names if indegree[n] == 0))
        order: list[str] = []
        while queue:
            node = queue.popleft()
            order.append(node)
            for nxt in sorted(adj.get(node, set())):
                indegree[nxt] -= 1
                if indegree[nxt] == 0:
                    queue.append(nxt)
        return order if len(order) == len(names) else []

    def _longest_path(self, topo: list[str], adj: dict[str, set[str]]) -> list[str]:
        best_len = {n: 1 for n in topo}
        prev: dict[str, str | None] = {n: None for n in topo}
        for node in topo:
            for nxt in adj.get(node, set()):
                if best_len[node] + 1 > best_len[nxt]:
                    best_len[nxt] = best_len[node] + 1
                    prev[nxt] = node
        if not best_len:
            return []
        end = max(best_len, key=best_len.get)
        path: list[str] = []
        cursor: str | None = end
        while cursor is not None:
            path.append(cursor)
            cursor = prev[cursor]
        return list(reversed(path))

    def _zone_uniformity(self, zones_by_module: dict[str, set[str]]) -> float:
        if not zones_by_module:
            return 0.0
        counts: dict[frozenset[str], int] = defaultdict(int)
        for zones in zones_by_module.values():
            counts[frozenset(zones)] += 1
        return max(counts.values()) / len(zones_by_module)

    def _entry_modules(self, spec: DiagramSpec, comp_to_mod: dict[str, str]) -> list[str]:
        seen: list[str] = []
        for ep in spec.entry_points:
            module = comp_to_mod.get(ep)
            if module and module not in seen:
                seen.append(module)
        return seen
