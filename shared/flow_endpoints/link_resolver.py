from shared.flow_endpoints.link_targets import EndpointLink
from shared.flow_endpoints.shared_helper_collapser import HELPER_PREFIX
from shared.flow_endpoints.terminal_closer import CONTINUE_PREFIX, LINK_PREFIX
from shared.models.flow_graph import FlowGraph, FlowNode


class LinkResolver:
    def resolve(
        self,
        sliced: FlowGraph,
        owners: dict[str, list[str]],
        current_root: str,
    ) -> dict[str, EndpointLink]:
        visible = [node for node in sliced.nodes if node.level == 0]
        successors = self._successors(sliced, {node.id for node in visible})
        resident = self._resident_owners(visible, successors)
        links: dict[str, EndpointLink] = {}
        for node in sorted(visible, key=lambda n: n.id):
            link = self._link_for(node, successors, resident, owners, current_root)
            if link is not None:
                links[node.id] = link
        return links

    def _link_for(
        self,
        node: FlowNode,
        successors: dict[str, set[str]],
        resident: set[str],
        owners: dict[str, list[str]],
        current_root: str,
    ) -> EndpointLink | None:
        label = node.llm_label or node.label
        if node.id.startswith(LINK_PREFIX):
            target = node.id[len(LINK_PREFIX):]
            if target == current_root:
                return None
            return EndpointLink(kind="endpoint", target=target, label=label)
        if node.id.startswith(HELPER_PREFIX):
            target = node.id[len(HELPER_PREFIX):]
            if target == current_root:
                return None
            return EndpointLink(kind="helper", target=target, label=label)
        if node.id.startswith(CONTINUE_PREFIX):
            target = node.id[len(CONTINUE_PREFIX):]
            if target == current_root:
                return None
            return EndpointLink(kind="helper", target=target, label=label)
        is_terminal = node.kind == "outcome" or not successors.get(node.id)
        if is_terminal and node.owner_fqn and len(owners.get(node.owner_fqn, [])) >= 2:
            if node.owner_fqn == current_root or node.owner_fqn in resident:
                return None
            return EndpointLink(kind="helper", target=node.owner_fqn, label=label)
        return None

    def _resident_owners(
        self,
        visible: list[FlowNode],
        successors: dict[str, set[str]],
    ) -> set[str]:
        return {
            node.owner_fqn
            for node in visible
            if node.owner_fqn and node.kind != "outcome" and successors.get(node.id)
        }

    def _successors(self, sliced: FlowGraph, visible_ids: set[str]) -> dict[str, set[str]]:
        successors: dict[str, set[str]] = {}
        for edge in sliced.edges:
            if edge.source in visible_ids and edge.target in visible_ids:
                successors.setdefault(edge.source, set()).add(edge.target)
        return successors
