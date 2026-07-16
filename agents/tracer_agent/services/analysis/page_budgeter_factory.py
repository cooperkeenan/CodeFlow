from services.analysis.arm_folder import ArmFolder
from services.analysis.budget_config import BudgetConfig
from services.analysis.budget_invariants import BudgetInvariantChecker
from services.analysis.budget_recondenser import BudgetRecondenser
from services.analysis.decision_admitter import DecisionAdmitter
from services.analysis.decision_dissolver import DecisionDissolver
from services.analysis.effect_capper import EffectCapper
from services.analysis.label_synthesizer import LabelSynthesizer
from services.analysis.lane_apportioner import LaneApportioner
from services.analysis.lane_reducer import LaneReducer
from services.analysis.page_budgeter import PageBudgeter


def build_page_budgeter(config: BudgetConfig | None = None) -> PageBudgeter:
    cfg = config or BudgetConfig()
    recondenser = BudgetRecondenser(LabelSynthesizer())
    return PageBudgeter(
        LaneApportioner(cfg),
        DecisionAdmitter(recondenser, DecisionDissolver(), LaneReducer()),
        ArmFolder(cfg),
        recondenser,
        EffectCapper(),
        BudgetInvariantChecker(cfg),
    )
