from models.node_naming import NodeNaming
from shared.models.flow_graph import FlowGraph

_LABEL_MAX_WORDS = 10
_ONE_LINER_MAX_CHARS = 120


class NameValidator:
    def validate(self, raw: dict, graph: FlowGraph) -> dict[str, NodeNaming]:
        node_ids = {node.id for node in graph.nodes}
        namings: dict[str, NodeNaming] = {}
        nodes = raw.get("nodes")
        if not isinstance(nodes, dict):
            return namings
        for node_id, value in nodes.items():
            if node_id not in node_ids or not isinstance(value, dict):
                continue
            label = self._cap_words(value.get("label"))
            one_liner = self._cap_chars(value.get("one_liner"))
            if label and one_liner:
                namings[node_id] = NodeNaming(label=label, one_liner=one_liner)
        return namings

    def _cap_words(self, value: object) -> str:
        if not isinstance(value, str):
            return ""
        words = value.strip().split()
        return " ".join(words[:_LABEL_MAX_WORDS])

    def _cap_chars(self, value: object) -> str:
        if not isinstance(value, str):
            return ""
        return value.strip()[:_ONE_LINER_MAX_CHARS]
