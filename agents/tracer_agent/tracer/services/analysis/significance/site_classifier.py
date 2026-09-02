from itertools import combinations

from tracer.models.sites import DispatchSite
from tracer.models.verdicts import ArmClass, Verdict

_STRUCTURAL_KINDS = frozenset({"route", "table", "polymorphic"})
_REACH_KINDS = frozenset({"branch", "match", "except"})


class SiteClassifier:
    def classify(
        self,
        site: DispatchSite,
        arm_classes: tuple[ArmClass, ...],
        reaches: tuple[frozenset[str], ...],
    ) -> Verdict:
        if site.kind in _STRUCTURAL_KINDS or site.kind == "dynamic":
            return "decision" if len(site.arms) >= 2 else "noise"
        if site.kind in _REACH_KINDS:
            return self._classify_reach(arm_classes, reaches)
        return "noise"

    def _classify_reach(
        self, arm_classes: tuple[ArmClass, ...], reaches: tuple[frozenset[str], ...]
    ) -> Verdict:
        live = [reaches[i] for i, cls in enumerate(arm_classes) if cls == "live"]
        if len(live) >= 2 and self._mutually_exclusive(live):
            return "decision"
        if len(live) == 1 and any(cls == "guard" for cls in arm_classes):
            return "guarded_step"
        return "noise"

    def _mutually_exclusive(self, live: list[frozenset[str]]) -> bool:
        for left, right in combinations(live, 2):
            if left <= right or right <= left:
                return False
        return True
