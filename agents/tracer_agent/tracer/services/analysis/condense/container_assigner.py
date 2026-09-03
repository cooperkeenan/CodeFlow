from tracer.services.analysis.condense.drafts import _NodeDraft
from tracer.services.analysis.condense.graph_accumulator import GraphAccumulator
from tracer.services.analysis.graph_ops import is_descendant, ref_sort_key


class ContainerAssigner:
    def assign(self, acc: GraphAccumulator) -> None:
        nodes = acc.nodes()
        by_owner: dict[str, list[str]] = {}
        for node_id in sorted(nodes):
            draft = nodes[node_id]
            if draft.arm_path:
                site_id = draft.arm_path[-1].split("#", 1)[0]
                acc.add_container(node_id, f"dec:{site_id}")
            elif draft.owner_fqn:
                by_owner.setdefault(draft.owner_fqn, []).append(node_id)
        heads: dict[str, str] = {}
        for owner in sorted(by_owner):
            heads[owner] = self._assign_body(acc, nodes, by_owner[owner])
        self._link_call_boundaries(acc, heads)
        self._link_effect_boundaries(acc, heads)

    def _assign_body(
        self, acc: GraphAccumulator, nodes: dict[str, _NodeDraft], members: list[str]
    ) -> str:
        head = min(members, key=lambda m: ref_sort_key(nodes, m))
        for member in members:
            if member != head:
                acc.add_container(member, head)
        return head

    def _link_call_boundaries(self, acc: GraphAccumulator, heads: dict[str, str]) -> None:
        nodes = acc.nodes()
        for caller_fqn, local_container, callee_fqn in sorted(acc.call_boundaries()):
            caller_head = local_container or heads.get(caller_fqn)
            callee_head = heads.get(callee_fqn)
            if caller_head is None or callee_head is None or caller_head == callee_head:
                continue
            container = self._nearest_safe_container(nodes, caller_head, callee_head)
            if container is not None:
                acc.add_container(callee_head, container)

    def _link_effect_boundaries(self, acc: GraphAccumulator, heads: dict[str, str]) -> None:
        nodes = acc.nodes()
        for caller_fqn, local_container, effect_id in sorted(acc.effect_boundaries()):
            caller_head = local_container or heads.get(caller_fqn)
            if caller_head is None or caller_head == effect_id:
                continue
            container = self._nearest_safe_container(nodes, caller_head, effect_id)
            if container is not None:
                acc.add_container(effect_id, container)

    def _nearest_safe_container(
        self, nodes: dict[str, _NodeDraft], start: str, target: str
    ) -> str | None:
        seen = {start}
        frontier = [start]
        while frontier:
            frontier.sort()
            for candidate in frontier:
                if not is_descendant(nodes, candidate, target):
                    return candidate
            next_frontier: list[str] = []
            for candidate in frontier:
                for container in nodes[candidate].containers:
                    if container not in seen:
                        seen.add(container)
                        next_frontier.append(container)
            frontier = next_frontier
        return None
