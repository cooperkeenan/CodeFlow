from shared.models.node_geometry import NODE_GEOMETRY

TARGET_ASPECT = 2.0
MAX_STRETCH = 1.8


class VerticalStretcher:
    def stretch(self, out_nodes: list[dict], hidden: list[dict]) -> None:
        factor = self._factor(out_nodes)
        if factor <= 1.0:
            return
        min_y = min(node["position"]["y"] for node in out_nodes)
        for node in out_nodes:
            position = node["position"]
            position["y"] = min_y + round((position["y"] - min_y) * factor)
        for node in out_nodes:
            self._scale_offsets(node, factor)
        for node in hidden:
            self._scale_offsets(node, factor)

    def _factor(self, out_nodes: list[dict]) -> float:
        if not out_nodes:
            return 1.0
        xs = [node["position"]["x"] for node in out_nodes]
        ys = [node["position"]["y"] for node in out_nodes]
        max_width = max(geometry.width for geometry in NODE_GEOMETRY.values())
        max_height = max(geometry.height for geometry in NODE_GEOMETRY.values())
        width = (max(xs) - min(xs)) + max_width
        height = (max(ys) - min(ys)) + max_height
        if height <= 0:
            return 1.0
        aspect = width / height
        return round(min(max(aspect / TARGET_ASPECT, 1.0), MAX_STRETCH), 3)

    def _scale_offsets(self, node: dict, factor: float) -> None:
        offsets = node.get("data", {}).get("hiddenChildren")
        if not offsets:
            return
        for offset in offsets:
            offset["dy"] = round(offset["dy"] * factor)
