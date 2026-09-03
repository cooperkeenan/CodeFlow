from tracer.services.analysis.budget.arm_folder import ArmFolder
from tracer.services.analysis.budget.budget_recondenser import BudgetRecondenser
from tracer.services.analysis.budget.container_repointer import ContainerRepointer
from tracer.services.analysis.budget.containment_indexer import ContainmentIndexer
from tracer.services.analysis.budget.containment_invariants import ContainmentInvariants
from tracer.services.analysis.budget.lane_apportioner import LaneApportioner
from tracer.services.analysis.budget.repo_root_anchor import RepoRootAnchor
from tracer.services.analysis.budget.reveal_chunker import RevealChunker
from tracer.services.analysis.budget.seed_anchor_folder import SeedAnchorFolder
from tracer.services.analysis.budget.sequence_chainer import SequenceChainer
from tracer.services.analysis.budget.skeleton_projector import SkeletonProjector
from tracer.services.analysis.budget.skeleton_reducer import SkeletonReducer
from tracer.services.analysis.budget.visibility_budgeter import VisibilityBudgeter
from tracer.services.analysis.config import BudgetConfig
from tracer.services.analysis.effects.effect_capper import EffectCapper
from tracer.services.analysis.ranking.pillar_gateway_selector import (
    PillarGatewaySelector,
)
from tracer.services.analysis.routes.label_synthesizer import LabelSynthesizer


def build_visibility_budgeter(config: BudgetConfig | None = None) -> VisibilityBudgeter:
    cfg = config or BudgetConfig()
    gateways = PillarGatewaySelector()
    repointer = ContainerRepointer()
    return VisibilityBudgeter(
        BudgetRecondenser(LabelSynthesizer(), repointer),
        ArmFolder(cfg, repointer),
        EffectCapper(repointer),
        LaneApportioner(cfg),
        SkeletonReducer(gateways),
        SkeletonProjector(),
        RevealChunker(cfg.max_reveal_per_node),
        SeedAnchorFolder(cfg.seed_anchors_per_lane),
        gateways,
        ContainmentInvariants(),
        RepoRootAnchor(),
        ContainmentIndexer(),
        SequenceChainer(),
        cfg.skeleton_budget,
    )
