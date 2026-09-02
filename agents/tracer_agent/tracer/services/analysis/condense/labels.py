from tracer.models.call_records import Arm
from tracer.models.sites import DispatchSite
from tracer.models.verdicts import SiteVerdict
from tracer.services.analysis.routes.label_synthesizer import LabelSynthesizer

_TERMINAL_WORDS = {
    "returns": "Returns",
    "raises": "Raises",
    "continues": "Continues",
}


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


class OutcomeLabeler:
    def label(self, arm: Arm, verdict: SiteVerdict | None) -> str:
        if verdict is not None and arm.index < len(verdict.arm_labels):
            candidate = verdict.arm_labels[arm.index]
            if candidate:
                return candidate
        if arm.label_source:
            return arm.label_source
        return _TERMINAL_WORDS.get(arm.terminal, arm.terminal)
