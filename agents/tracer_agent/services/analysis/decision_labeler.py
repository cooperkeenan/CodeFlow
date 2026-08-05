from models.arm import Arm
from models.dispatch_site import DispatchSite
from models.site_verdict import SiteVerdict
from services.analysis.label_synthesizer import LabelSynthesizer


class DecisionLabeler:
    def __init__(self, labels: LabelSynthesizer) -> None:
        self._labels = labels

    def decision_label(self, site: DispatchSite, verdict: SiteVerdict | None) -> str:
        if verdict is not None and verdict.question:
            return verdict.question
        return self._labels.decision_label(site.selector_source)

    def arm_label(self, arm: Arm, verdict: SiteVerdict | None) -> str:
        if verdict is not None and arm.index < len(verdict.arm_labels):
            candidate = verdict.arm_labels[arm.index]
            if candidate:
                return candidate
        return arm.label_source
