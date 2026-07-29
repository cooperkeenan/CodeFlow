from models.significance_result import SignificanceResult
from services.analysis.arm_folder import ArmFolder
from services.analysis.budget_invariants import BudgetInvariantChecker
from services.analysis.budget_recondenser import BudgetRecondenser
from services.analysis.budget_work_graph import BudgetWorkGraph
from services.analysis.decision_admitter import DecisionAdmitter
from services.analysis.effect_capper import EffectCapper
from services.analysis.lane_apportioner import LaneApportioner
from shared.models.flow_graph import FlowGraph


class PageBudgeter:
    def __init__(
        self,
        apportioner: LaneApportioner,
        admitter: DecisionAdmitter,
        folder: ArmFolder,
        recondenser: BudgetRecondenser,
        capper: EffectCapper,
        checker: BudgetInvariantChecker,
    ) -> None:
        self._apportioner = apportioner
        self._admitter = admitter
        self._folder = folder
        self._recondenser = recondenser
        self._capper = capper
        self._checker = checker

    def budget(self, graph: FlowGraph, significance: SignificanceResult) -> FlowGraph:
        work = BudgetWorkGraph(graph)
        budgets = self._apportioner.apportion(work.lanes)
        self._admitter.admit(work, budgets, significance)
        self._folder.fold(work)
        self._recondenser.recondense(work)
        self._capper.cap(work)
        self._admitter.sweep_orphaned(work)
        self._checker.enforce(work)
        return work.to_flow_graph()
