from models.arm import Arm
from models.site_verdict import ArmClass
from services.analysis.significance_config import SignificanceConfig

_GUARD_TERMINALS = frozenset({"raises", "returns", "continues"})


class ArmClassifier:
    def __init__(self, config: SignificanceConfig) -> None:
        self._config = config

    def classify(self, arm: Arm, reach: frozenset[str]) -> ArmClass:
        if arm.terminal in _GUARD_TERMINALS and len(reach) <= self._config.guard_reach_limit:
            return "guard"
        if not reach:
            return "void"
        return "live"
