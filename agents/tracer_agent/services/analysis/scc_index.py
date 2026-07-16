from collections.abc import Mapping


class SccIndex:
    def __init__(self, component_of_node: Mapping[str, int], members: Mapping[int, frozenset[str]]) -> None:
        self._component_of_node = component_of_node
        self._members = members

    def scc_of(self, fqn: str) -> int | None:
        return self._component_of_node.get(fqn)

    def members_of(self, scc_id: int) -> frozenset[str]:
        return self._members.get(scc_id, frozenset())
