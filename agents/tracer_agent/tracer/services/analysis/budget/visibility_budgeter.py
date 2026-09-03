from tracer.models.pillar_scores import PillarScores
from tracer.services.analysis.budget.arm_folder import ArmFolder
from tracer.services.analysis.budget.containment_invariants import ContainmentInvariants
from tracer.services.analysis.budget.budget_recondenser import BudgetRecondenser
from tracer.services.analysis.budget.budget_work_graph import BudgetWorkGraph
from tracer.services.analysis.budget.containment_indexer import ContainmentIndexer
from tracer.services.analysis.budget.lane_apportioner import LaneApportioner
from tracer.services.analysis.budget.repo_root_anchor import RepoRootAnchor
from tracer.services.analysis.budget.reveal_chunker import RevealChunker
from tracer.services.analysis.budget.seed_anchor_folder import SeedAnchorFolder
from tracer.services.analysis.budget.sequence_chainer import SequenceChainer
from tracer.services.analysis.budget.skeleton_projector import SkeletonProjector
from tracer.services.analysis.budget.skeleton_reducer import SkeletonReducer
from tracer.services.analysis.effects.effect_capper import EffectCapper
from tracer.services.analysis.ranking.pillar_gateway_selector import (
    PillarGatewaySelector,
)
from tracer.services.analysis.resolve.indexes import ComponentIndex

from shared.models.flow_graph import FlowGraph


class VisibilityBudgeter:
    def __init__(
        self,
        recondenser: BudgetRecondenser,
        folder: ArmFolder,
        capper: EffectCapper,
        apportioner: LaneApportioner,
        reducer: SkeletonReducer,
        projector: SkeletonProjector,
        chunker: RevealChunker,
        seeds: SeedAnchorFolder,
        gateways: PillarGatewaySelector,
        checker: ContainmentInvariants,
        root_anchor: RepoRootAnchor,
        indexer: ContainmentIndexer,
        sequencer: SequenceChainer,
        skeleton_budget: int,
    ) -> None:
        self._recondenser = recondenser
        self._folder = folder
        self._capper = capper
        self._apportioner = apportioner
        self._reducer = reducer
        self._projector = projector
        self._chunker = chunker
        self._seeds = seeds
        self._gateways = gateways
        self._checker = checker
        self._root_anchor = root_anchor
        self._indexer = indexer
        self._sequencer = sequencer
        self._skeleton_budget = skeleton_budget

    def budget(
        self, graph: FlowGraph, pillars: PillarScores, components: ComponentIndex
    ) -> FlowGraph:
        work = BudgetWorkGraph(graph)
        self._recondenser.recondense(work)
        self._folder.fold(work)
        self._capper.cap(work)
        self._root_anchor.anchor(work)
        self._sequencer.link(work)
        self._indexer.index(work)
        self._checker.enforce_structure(work)
        self._seeds.fold(work, pillars)
        gateway_ids = self._gateways.select(work, pillars, components)
        budgets = self._apportioner.apportion(work.lanes)
        root_id = f"root:{work.repo}"
        promoted: set[str] = set()
        for lane in sorted(work.lanes, key=lambda lane: lane.id):
            promoted |= self._reducer.reduce(
                work, lane.id, budgets.get(lane.id, 0), pillars, gateway_ids, components, root_id
            )
        promoted = self._reducer.reduce_global(
            work, self._skeleton_budget, pillars, gateway_ids, components, root_id, promoted
        )
        skeleton_ids = frozenset(promoted)
        self._indexer.index(work, skeleton_ids)
        for edge in self._projector.project(work):
            work.upsert_hidden_edge(edge)
        hidden_children = {
            node_id: work.nodes[node_id].hidden_children
            for node_id in sorted(work.nodes)
            if work.nodes[node_id].hidden_children
        }
        chunked = self._chunker.chunk(work, hidden_children)
        for node_id, children in sorted(chunked.items()):
            work.nodes[node_id].hidden_children = children
        self._indexer.relevel(work, skeleton_ids)
        self._checker.enforce_structure(work)
        self._checker.enforce_bodies(work)
        result = work.to_flow_graph()
        result.meta["skeleton_nodes"] = sum(1 for n in result.nodes if n.level == 0)
        result.meta["revealed_nodes"] = sum(1 for n in result.nodes if n.level >= 1)
        result.meta["border_edges"] = self._checker.border_count(work)
        flow, lst = self._checker.flow_list_split(work)
        result.meta["flow_bodies"] = flow
        result.meta["list_bodies"] = lst
        return result
