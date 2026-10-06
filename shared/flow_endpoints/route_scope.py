from dataclasses import dataclass, field

from shared.models.flow_graph import FlowEdge, FlowNode, RouteMember

_WALKABLE = {"sequence", "arm", "parallel"}
_MAX_OWNED = 80
_MAX_REGION = 60


@dataclass
class RouteScopeResult:
    ids: set[str]
    regions: dict[str, list[str]] = field(default_factory=dict)


class RouteScope:
    def of(
        self, nodes: dict[str, FlowNode], edges: list[FlowEdge], root: FlowNode, member: RouteMember
    ) -> RouteScopeResult:
        path = [i for i in (member.happy.node_ids if member.happy else []) if i in nodes]
        hops = [h for h in (member.happy.hops if member.happy else []) if h in nodes]
        owners = self._owners(nodes, member, set(hops))
        successors = self._successors(edges)
        path_set = set(path) | {root.id}
        owned = self._owned(nodes, successors, owners, path_set, set(hops))
        regions = {
            hop: self._region(nodes, successors, owners, path_set, hop) for hop in sorted(hops)
        }
        ids = path_set | owned | {n for region in regions.values() for n in region}
        ids |= self._context(nodes, successors, owners, ids, set(hops))
        return RouteScopeResult(ids, regions)

    def _owners(self, nodes: dict[str, FlowNode], member: RouteMember, hops: set[str]) -> set[str]:
        owners = {member.handler_fqn}
        head = nodes.get(member.head)
        if head is not None and head.owner_fqn and head.id not in hops:
            owners.add(head.owner_fqn)
        return owners

    def _successors(self, edges: list[FlowEdge]) -> dict[str, list[str]]:
        found: dict[str, set[str]] = {}
        for edge in edges:
            if edge.kind in _WALKABLE:
                found.setdefault(edge.source, set()).add(edge.target)
        return {source: sorted(targets) for source, targets in found.items()}

    def _owned(
        self,
        nodes: dict[str, FlowNode],
        successors: dict[str, list[str]],
        owners: set[str],
        path_set: set[str],
        hops: set[str],
    ) -> set[str]:
        found: set[str] = set()
        queue = sorted(path_set - hops)
        while queue and len(found) < _MAX_OWNED:
            current = queue.pop(0)
            for target in successors.get(current, []):
                node = nodes.get(target)
                if node is None or node.kind == "entry" or target in found or target in path_set:
                    continue
                if node.owner_fqn in owners:
                    found.add(target)
                    queue.append(target)
        return found

    def _region(
        self,
        nodes: dict[str, FlowNode],
        successors: dict[str, list[str]],
        owners: set[str],
        path_set: set[str],
        hop: str,
    ) -> list[str]:
        region = [hop]
        seen = {hop}
        queue = [hop]
        while queue and len(region) < _MAX_REGION:
            current = queue.pop(0)
            for target in successors.get(current, []):
                node = nodes.get(target)
                if node is None or node.kind == "entry" or target in seen or target in path_set:
                    continue
                if node.owner_fqn in owners:
                    continue
                seen.add(target)
                region.append(target)
                queue.append(target)
        return region

    def _context(
        self,
        nodes: dict[str, FlowNode],
        successors: dict[str, list[str]],
        owners: set[str],
        ids: set[str],
        hops: set[str],
    ) -> set[str]:
        found: set[str] = set()
        for node_id in sorted(ids - hops):
            if nodes[node_id].owner_fqn not in owners:
                continue
            for target in successors.get(node_id, []):
                node = nodes.get(target)
                if node is not None and node.kind != "entry" and target not in ids:
                    found.add(target)
        return found
