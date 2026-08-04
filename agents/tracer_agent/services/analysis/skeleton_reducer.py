from models.pillar_scores import PillarScores
from services.analysis.budget_work_graph import BudgetWorkGraph
from services.analysis.component_index import ComponentIndex
from services.analysis.pillar_gateway_selector import PillarGatewaySelector
from shared.models.flow_graph import FlowNode

_KIND_RANK = {"effect": 0, "parallel": 1, "step": 2, "decision": 3, "entry": 4}


class SkeletonReducer:
    def __init__(self, gateways: PillarGatewaySelector) -> None:
        self._gateways = gateways

    def reduce(
        self,
        graph: BudgetWorkGraph,
        lane_id: str,
        budget: int,
        pillars: PillarScores,
        gateway_ids: frozenset[str],
        components: ComponentIndex,
        root_id: str,
    ) -> set[str]:
        ranked = self._ranked(
            self._candidates(graph, root_id, lane_id), graph, pillars, gateway_ids, components, True
        )
        return {node.id for node in ranked[:budget]}

    def reduce_global(
        self,
        graph: BudgetWorkGraph,
        budget: int,
        pillars: PillarScores,
        gateway_ids: frozenset[str],
        components: ComponentIndex,
        root_id: str,
        promoted: set[str],
    ) -> set[str]:
        if len(promoted) > budget:
            return self._demote_fairly(
                graph, promoted, len(promoted) - budget, pillars, gateway_ids, components
            )
        if len(promoted) < budget:
            candidates = [
                node
                for node in self._candidates(graph, root_id, None)
                if node.id not in promoted
            ]
            strongest = self._ranked(candidates, graph, pillars, gateway_ids, components, True)
            extra = {node.id for node in strongest[: budget - len(promoted)]}
            return promoted | extra
        return promoted

    def _demote_fairly(
        self,
        graph: BudgetWorkGraph,
        promoted: set[str],
        excess: int,
        pillars: PillarScores,
        gateway_ids: frozenset[str],
        components: ComponentIndex,
    ) -> set[str]:
        keep = set(promoted)
        by_lane: dict[str, list[str]] = {}
        for node_id in keep:
            by_lane.setdefault(graph.nodes[node_id].lane, []).append(node_id)
        for _ in range(excess):
            lane_id = max(by_lane, key=lambda lid: (len(by_lane[lid]), lid))
            lane_nodes = by_lane[lane_id]
            weakest = min(
                lane_nodes,
                key=lambda nid: self._rank(
                    graph, graph.nodes[nid], pillars, gateway_ids, components
                ),
            )
            keep.discard(weakest)
            lane_nodes.remove(weakest)
            if not lane_nodes:
                del by_lane[lane_id]
        return keep

    def _candidates(
        self, graph: BudgetWorkGraph, root_id: str, lane_id: str | None
    ) -> list[FlowNode]:
        return [
            node
            for node in graph.nodes.values()
            if node.containers == [root_id] and (lane_id is None or node.lane == lane_id)
        ]

    def _ranked(
        self,
        nodes: list[FlowNode],
        graph: BudgetWorkGraph,
        pillars: PillarScores,
        gateway_ids: frozenset[str],
        components: ComponentIndex,
        strongest_first: bool,
    ) -> list[FlowNode]:
        return sorted(
            nodes,
            key=lambda node: self._rank(graph, node, pillars, gateway_ids, components),
            reverse=strongest_first,
        )

    def _rank(
        self,
        graph: BudgetWorkGraph,
        node: FlowNode,
        pillars: PillarScores,
        gateway_ids: frozenset[str],
        components: ComponentIndex,
    ) -> tuple[int, float, int, int, int, str]:
        component = self._gateways.component_of(node, components)
        return (
            1 if node.id in gateway_ids else 0,
            pillars.score(component),
            _KIND_RANK.get(node.kind, 0),
            len(graph.out_edges(node.id)),
            len(node.backing),
            node.id,
        )
