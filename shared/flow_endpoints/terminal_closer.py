from shared.flow_endpoints.slice_graph import SliceGraph
from shared.models.flow_graph import FlowNode

LINK_PREFIX = "endlink:"
OUTCOME_PREFIX = "endout:"

_EFFECT_WORDS = {
    "response": "Returns a response",
    "database": "Writes to the database",
    "http_out": "Calls an external service",
    "llm": "Calls the model",
    "file": "Writes a file",
    "queue": "Queues work",
    "email": "Sends email",
}


class TerminalCloser:
    def __init__(self, outside: dict[str, FlowNode], entry_ids: frozenset[str]) -> None:
        self._outside = outside
        self._entries = entry_ids

    def close(self, graph: SliceGraph) -> int:
        added = 0
        for node_id in sorted(graph.keep):
            if self._has_continuation(graph, node_id):
                continue
            terminal = self._terminal_for(graph, node_id)
            graph.add_node(terminal)
            graph.add_edge(node_id, terminal.id)
            added += 1
        return added

    def _has_continuation(self, graph: SliceGraph, node_id: str) -> bool:
        node = graph.nodes[node_id]
        if node.kind == "outcome" or node.hidden_children:
            return True
        return any(target in graph.keep for target in graph.successors(node_id))

    def _terminal_for(self, graph: SliceGraph, node_id: str) -> FlowNode:
        node = graph.nodes[node_id]
        outside = [
            self._outside[target]
            for target in graph.external.get(node_id, [])
            if target in self._outside
        ]
        linked = [candidate for candidate in outside if candidate.id in self._entries]
        if linked:
            target = linked[0]
            label = f"Continues in {target.llm_label or target.label}"
            return self._node(f"{LINK_PREFIX}{target.id}", node, label)
        return self._node(f"{OUTCOME_PREFIX}{node_id}", node, self._label(node, outside))

    def _label(self, node: FlowNode, outside: list[FlowNode]) -> str:
        for candidate in outside:
            if candidate.kind == "effect" and candidate.effect_kind in _EFFECT_WORDS:
                return _EFFECT_WORDS[candidate.effect_kind]
        if outside:
            return "Continues"
        return "Continues" if node.kind == "decision" else "Returns"

    def _node(self, node_id: str, source: FlowNode, label: str) -> FlowNode:
        return FlowNode(
            id=node_id,
            kind="outcome",
            lane=source.lane,
            label=label,
            llm_label=label,
            refs=list(source.refs[:1]),
            owner_fqn=source.owner_fqn,
        )
