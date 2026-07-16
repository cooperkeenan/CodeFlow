from models.flow_label_maps import FlowLabelMaps
from prompts.flow_label_prompt import arm_key_map
from shared.models.flow_graph import FlowGraph

_NODE_LABEL_MAX_WORDS = 6
_ARM_MAX_WORDS = 4
_ONE_LINER_MAX_CHARS = 120
_TITLE_MAX_CHARS = 60


class FlowLabelValidator:
    def validate(self, raw: dict, graph: FlowGraph) -> FlowLabelMaps:
        node_ids = {node.id for node in graph.nodes}
        lane_ids = {lane.id for lane in graph.lanes}
        arm_keys = set(arm_key_map(graph).keys())

        node_labels, node_one_liners = self._nodes(raw.get("nodes"), node_ids)
        return FlowLabelMaps(
            page_title=self._words_or_chars(raw.get("page_title"), _TITLE_MAX_CHARS),
            lane_titles=self._titles(raw.get("lanes"), lane_ids),
            node_labels=node_labels,
            node_one_liners=node_one_liners,
            arm_labels=self._arms(raw.get("arms"), arm_keys),
        )

    def _nodes(self, raw: object, node_ids: set[str]) -> tuple[dict[str, str], dict[str, str]]:
        labels: dict[str, str] = {}
        one_liners: dict[str, str] = {}
        if not isinstance(raw, dict):
            return labels, one_liners
        for node_id, value in raw.items():
            if node_id not in node_ids or not isinstance(value, dict):
                continue
            label = self._cap_words(value.get("label"), _NODE_LABEL_MAX_WORDS)
            if label:
                labels[node_id] = label
            one_liner = self._words_or_chars(value.get("one_liner"), _ONE_LINER_MAX_CHARS)
            if one_liner:
                one_liners[node_id] = one_liner
        return labels, one_liners

    def _titles(self, raw: object, lane_ids: set[str]) -> dict[str, str]:
        titles: dict[str, str] = {}
        if not isinstance(raw, dict):
            return titles
        for lane_id, value in raw.items():
            if lane_id not in lane_ids:
                continue
            title = self._words_or_chars(value, _TITLE_MAX_CHARS)
            if title:
                titles[lane_id] = title
        return titles

    def _arms(self, raw: object, arm_keys: set[str]) -> dict[str, str]:
        arms: dict[str, str] = {}
        if not isinstance(raw, dict):
            return arms
        for key, value in raw.items():
            if key not in arm_keys:
                continue
            label = self._cap_words(value, _ARM_MAX_WORDS)
            if label:
                arms[key] = label
        return arms

    def _cap_words(self, value: object, max_words: int) -> str:
        if not isinstance(value, str):
            return ""
        words = value.strip().split()
        return " ".join(words[:max_words])

    def _words_or_chars(self, value: object, max_chars: int) -> str:
        if not isinstance(value, str):
            return ""
        text = value.strip()
        return text[:max_chars]
