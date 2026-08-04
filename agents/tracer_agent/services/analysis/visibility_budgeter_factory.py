from services.analysis.arm_folder import ArmFolder
from services.analysis.budget_config import BudgetConfig
from services.analysis.budget_invariants import BudgetInvariantChecker
from services.analysis.budget_recondenser import BudgetRecondenser
from services.analysis.containment_indexer import ContainmentIndexer
from services.analysis.containment_invariants import ContainmentInvariants
from services.analysis.effect_capper import EffectCapper
from services.analysis.label_synthesizer import LabelSynthesizer
from services.analysis.lane_apportioner import LaneApportioner
from services.analysis.repo_root_anchor import RepoRootAnchor
from services.analysis.reveal_chunker import RevealChunker
from services.analysis.pillar_gateway_selector import PillarGatewaySelector
from services.analysis.seed_anchor_folder import SeedAnchorFolder
from services.analysis.skeleton_projector import SkeletonProjector
from services.analysis.skeleton_reducer import SkeletonReducer
from services.analysis.visibility_budgeter import VisibilityBudgeter


def build_visibility_budgeter(config: BudgetConfig | None = None) -> VisibilityBudgeter:
    cfg = config or BudgetConfig()
    gateways = PillarGatewaySelector()
    return VisibilityBudgeter(
        BudgetRecondenser(LabelSynthesizer()),
        ArmFolder(cfg),
        EffectCapper(),
        LaneApportioner(cfg),
        SkeletonReducer(gateways),
        SkeletonProjector(),
        RevealChunker(cfg.max_reveal_per_node),
        SeedAnchorFolder(cfg.seed_anchors_per_lane),
        gateways,
        BudgetInvariantChecker(ContainmentInvariants()),
        RepoRootAnchor(),
        ContainmentIndexer(),
        cfg.skeleton_budget,
    )
