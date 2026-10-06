from tracer.services.analysis.paths.candidate_ranker import CandidateRanker
from tracer.services.analysis.paths.hop_finder import HopFinder
from tracer.services.analysis.paths.path_graph import PathGraph
from tracer.services.analysis.paths.route_owners import RouteOwners

from shared.models.flow_graph import FlowNode, HappyPath, RouteMember


class HappyPathWalker:
    def __init__(
        self, graph: PathGraph, ranker: CandidateRanker, hops: HopFinder, route_owners: RouteOwners
    ) -> None:
        self._route_owners = route_owners
        self._graph = graph
        self._ranker = ranker
        self._hops = hops

    def walk(self, entry_id: str, member: RouteMember) -> HappyPath:
        head = self._graph.node(member.head)
        path = [entry_id]
        if head is None:
            return HappyPath(node_ids=path)
        visited = {entry_id}
        failed = self._wrapper_phase(entry_id, member, path, visited)
        if not self._links_to(path[-1], head.id):
            return HappyPath(node_ids=path, ends_in_failure=failed)
        path.append(head.id)
        visited.add(head.id)
        owners = self._route_owners.of(member.handler_fqn)
        hops: list[str] = []
        failed = self._handler_phase(head, member, owners, path, visited, hops) or failed
        return HappyPath(node_ids=path, hops=hops, ends_in_failure=failed)

    def _wrapper_phase(
        self, entry_id: str, member: RouteMember, path: list[str], visited: set[str]
    ) -> bool:
        owners = frozenset(member.wrappers)
        failed = False
        while owners and not self._links_to(path[-1], member.head):
            edges = [
                e
                for e in self._graph.out(path[-1])
                if e.target not in visited
                and self._graph.owner(e.target) in owners
                and self._graph.is_walkable_target(e.target, member.head)
            ]
            edge, forced = self._ranker.choose(edges, owners, visited, member.method, member.head)
            if edge is None:
                break
            failed = failed or forced
            path.append(edge.target)
            visited.add(edge.target)
        return failed

    def _handler_phase(
        self,
        head: FlowNode,
        member: RouteMember,
        owners: frozenset[str],
        path: list[str],
        visited: set[str],
        hops: list[str],
    ) -> bool:
        failed = False
        pred_line = self._graph.line(head.id)
        current = head
        while True:
            owned = current.owner_fqn in owners
            if owned:
                pred_line = self._graph.line(current.id)
            else:
                hops.append(current.id)
            if current.kind == "outcome" or current.effect_kind == "response":
                break
            if owned:
                edges = [
                    e
                    for e in self._graph.out(current.id)
                    if e.target not in visited
                    and self._graph.is_walkable_target(e.target, head.id)
                ]
                edge, forced = self._ranker.choose(edges, owners, visited, member.method, head.id)
                target = edge.target if edge else None
                failed = failed or forced
            else:
                target = self._hops.resume(current.id, owners, visited, head.id, pred_line)
            if target is None:
                break
            path.append(target)
            visited.add(target)
            current = self._graph.node(target)
        return failed

    def _links_to(self, source: str, target: str) -> bool:
        return any(e.target == target for e in self._graph.out(source))
