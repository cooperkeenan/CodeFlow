from shared.flow_endpoints.chunk_dissolver import ChunkDissolver
from shared.flow_endpoints.endpoint_ranker import EndpointRanker
from shared.flow_endpoints.fanout_capper import FanoutCapper
from shared.flow_endpoints.island_demoter import IslandDemoter
from shared.flow_endpoints.run_collapser import RunCollapser
from shared.flow_endpoints.shared_helper_collapser import SharedHelperCollapser
from shared.flow_endpoints.sole_child_promoter import SoleChildPromoter
from shared.flow_endpoints.level_assigner import LevelAssigner
from shared.flow_endpoints.slice_graph import SliceGraph
from shared.flow_endpoints.terminal_closer import TerminalCloser

DEFAULT_BUDGET = 16
_MAX_PASSES = 3


class EndpointElider:
    def __init__(
        self,
        dissolver: ChunkDissolver,
        level_assigner: LevelAssigner,
        capper: FanoutCapper | None = None,
        islands: IslandDemoter | None = None,
        runs: RunCollapser | None = None,
        helpers: SharedHelperCollapser | None = None,
        promoter: SoleChildPromoter | None = None,
        budget: int = DEFAULT_BUDGET,
    ) -> None:
        self._dissolver = dissolver
        self._levels = level_assigner
        self._capper = capper or FanoutCapper()
        self._islands = islands or IslandDemoter()
        self._runs = runs or RunCollapser()
        self._helpers = helpers or SharedHelperCollapser()
        self._promoter = promoter or SoleChildPromoter()
        self._budget = budget

    def elide(
        self,
        graph: SliceGraph,
        exclusivity: dict[str, int],
        closer: TerminalCloser,
    ) -> None:
        self._dissolver.dissolve(graph)
        self._helpers.collapse(graph, exclusivity)
        self._runs.collapse(graph)
        self._reduce(graph, exclusivity, closer)
        self._promoter.promote(graph, self._levels)

    def _reduce(
        self,
        graph: SliceGraph,
        exclusivity: dict[str, int],
        closer: TerminalCloser,
    ) -> None:
        original = set(graph.keep)
        headroom = 0
        for _ in range(_MAX_PASSES):
            graph.keep = self._selected(graph, original, exclusivity, headroom)
            self._levels.assign(graph)
            added = closer.close(graph)
            self._levels.assign(graph)
            if len(graph.keep) <= self._budget or added == 0:
                return
            headroom = len(graph.keep) - self._budget

    def _selected(
        self,
        graph: SliceGraph,
        original: set[str],
        exclusivity: dict[str, int],
        headroom: int,
    ) -> set[str]:
        graph.keep = {node_id for node_id in original if node_id in graph.nodes}
        self._islands.demote(graph)
        self._capper.cap(graph)
        if len(graph.keep) <= self._budget - headroom:
            return graph.keep
        return EndpointRanker(exclusivity).select(graph, self._budget - headroom)
