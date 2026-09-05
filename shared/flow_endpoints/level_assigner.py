from shared.flow_endpoints.slice_graph import SliceGraph
from shared.models.flow_graph import FlowNode


class LevelAssigner:
    def assign(self, graph: SliceGraph) -> None:
        hosts = self._hosts(graph)
        bodies: dict[str, list[str]] = {}
        for node_id in sorted(graph.nodes):
            host = hosts.get(node_id)
            if host is not None:
                bodies.setdefault(host, []).append(node_id)
        order = self._distance(graph)
        for host_id, members in bodies.items():
            members.sort(key=lambda member: (order.get(member, 10**6), member))
        for node_id, node in graph.nodes.items():
            node.level = self._level(node_id, hosts)
            node.hidden_children = bodies.get(node_id, [])
            self._shape_body(graph, node, bodies.get(node_id, []))

    def _hosts(self, graph: SliceGraph) -> dict[str, str]:
        order = self._distance(graph)
        hidden = [node_id for node_id in sorted(graph.nodes) if node_id not in graph.keep]
        hosts: dict[str, str] = {}
        for node_id in hidden:
            host = self._visible_host(graph, node_id, order)
            if host is not None:
                hosts[node_id] = host
        pending = [node_id for node_id in hidden if node_id not in hosts]
        for _ in range(len(pending) + 1):
            progressed = False
            for node_id in list(pending):
                parents = self._parents(graph, node_id, order)
                nested = next((p for p in parents if p in hosts), None)
                if nested is not None:
                    hosts[node_id] = nested
                    pending.remove(node_id)
                    progressed = True
            if not progressed:
                break
        for node_id in pending:
            hosts[node_id] = graph.root_id
        return hosts

    def _visible_host(
        self, graph: SliceGraph, node_id: str, order: dict[str, int]
    ) -> str | None:
        for parent in self._parents(graph, node_id, order):
            if parent in graph.keep:
                return parent
        return None

    def _parents(self, graph: SliceGraph, node_id: str, order: dict[str, int]) -> list[str]:
        preds = sorted(
            graph.predecessors(node_id), key=lambda p: (order.get(p, 10**6), p)
        )
        containers = [c for c in graph.nodes[node_id].containers if c in graph.nodes]
        return preds + [c for c in containers if c not in preds]

    def _level(self, node_id: str, hosts: dict[str, str]) -> int:
        level = 0
        seen = {node_id}
        current = node_id
        while current in hosts:
            current = hosts[current]
            level += 1
            if current in seen or level > 32:
                break
            seen.add(current)
        return level

    def _distance(self, graph: SliceGraph) -> dict[str, int]:
        distance = {graph.root_id: 0}
        frontier = [graph.root_id]
        while frontier:
            nxt: list[str] = []
            for node_id in frontier:
                for target in graph.successors(node_id):
                    if target not in distance:
                        distance[target] = distance[node_id] + 1
                        nxt.append(target)
            frontier = nxt
        return distance

    def _shape_body(self, graph: SliceGraph, node: FlowNode, members: list[str]) -> None:
        if not members:
            node.body_head = ""
            node.body_tails = []
            node.body_kind = "flow"
            return
        member_set = set(members)
        internal = [e for e in graph.edges if e.source in member_set and e.target in member_set]
        heads = [m for m in members if not any(e.target == m for e in internal)]
        tails = [m for m in members if not any(e.source == m for e in internal)]
        node.body_kind = "flow" if len(internal) >= len(members) - 1 else "list"
        node.body_head = heads[0] if len(heads) == 1 else ""
        node.body_tails = tails
