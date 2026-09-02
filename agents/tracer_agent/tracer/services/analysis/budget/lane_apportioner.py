import math

from tracer.services.analysis.config import BudgetConfig

from shared.models.flow_graph import Lane


class LaneApportioner:
    def __init__(self, config: BudgetConfig) -> None:
        self._config = config

    def apportion(self, lanes: list[Lane]) -> dict[str, int]:
        if not lanes:
            return {}
        total = sum(lane.mass for lane in lanes)
        base = self._base(lanes, total)
        remainder = self._config.node_budget - sum(base.values())
        for lane in self._mass_order(lanes)[: max(remainder, 0)]:
            base[lane.id] += 1
        return {lane.id: max(self._config.min_lane_nodes, base[lane.id]) for lane in lanes}

    def _base(self, lanes: list[Lane], total: float) -> dict[str, int]:
        if total <= 0:
            share = self._config.node_budget // len(lanes)
            return {lane.id: share for lane in lanes}
        return {
            lane.id: math.floor(self._config.node_budget * lane.mass / total) for lane in lanes
        }

    def _mass_order(self, lanes: list[Lane]) -> list[Lane]:
        return sorted(lanes, key=lambda lane: (-lane.mass, lane.id))
