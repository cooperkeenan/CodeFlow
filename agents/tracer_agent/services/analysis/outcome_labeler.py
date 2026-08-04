from models.arm import Arm
from models.site_verdict import SiteVerdict

_TERMINAL_WORDS = {
    "returns": "Returns",
    "raises": "Raises",
    "continues": "Continues",
}


class OutcomeLabeler:
    def label(self, arm: Arm, verdict: SiteVerdict | None) -> str:
        if verdict is not None and arm.index < len(verdict.arm_labels):
            candidate = verdict.arm_labels[arm.index]
            if candidate:
                return candidate
        if arm.label_source:
            return arm.label_source
        return _TERMINAL_WORDS.get(arm.terminal, arm.terminal)
