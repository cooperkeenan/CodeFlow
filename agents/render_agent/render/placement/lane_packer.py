from shared.models.flow_graph import FlowGraph


class LanePacker:
    def order(self, graph: FlowGraph) -> list[str]:
        seed = [
            lane.id
            for lane in sorted(graph.lanes, key=lambda lane: (-lane.mass, lane.id))
        ]
        stitches = self._stitch_pairs(graph)
        if not stitches:
            return seed
        return self._minimize(seed, stitches)

    def _stitch_pairs(self, graph: FlowGraph) -> list[tuple[str, str]]:
        lane_of = {node.id: node.lane for node in graph.nodes}
        pairs: list[tuple[str, str]] = []
        for edge in graph.edges:
            if edge.kind != "stitch":
                continue
            source_lane = lane_of.get(edge.source)
            target_lane = lane_of.get(edge.target)
            if source_lane and target_lane and source_lane != target_lane:
                pairs.append((source_lane, target_lane))
        return pairs

    def _cost(self, order: list[str], stitches: list[tuple[str, str]]) -> int:
        position = {lane_id: index for index, lane_id in enumerate(order)}
        spans = [tuple(sorted((position[a], position[b]))) for a, b in stitches]
        crossings = 0
        for i in range(len(spans)):
            for j in range(i + 1, len(spans)):
                lo1, hi1 = spans[i]
                lo2, hi2 = spans[j]
                if lo1 < lo2 < hi1 < hi2 or lo2 < lo1 < hi2 < hi1:
                    crossings += 1
        return crossings

    def _minimize(
        self, seed: list[str], stitches: list[tuple[str, str]]
    ) -> list[str]:
        order = list(seed)
        improved = True
        while improved:
            improved = False
            for index in range(len(order) - 1):
                swapped = list(order)
                swapped[index], swapped[index + 1] = swapped[index + 1], swapped[index]
                if self._cost(swapped, stitches) < self._cost(order, stitches):
                    order = swapped
                    improved = True
        return order
