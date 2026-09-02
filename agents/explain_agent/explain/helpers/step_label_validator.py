from explain.models.step_input import StepInput

_MAX_STEP_LABEL_WORDS = 5
_LOCKED_KINDS = frozenset({"return", "raise"})


class StepLabelValidator:
    def validate(self, raw: object, steps: list[StepInput]) -> dict[str, str]:
        raw_map = raw if isinstance(raw, dict) else {}
        result: dict[str, str] = {}
        for step in steps:
            if step.kind in _LOCKED_KINDS:
                result[step.id] = step.label
                continue
            result[step.id] = self._clamp(raw_map.get(step.id)) or step.label
        return result

    def _clamp(self, value: object) -> str:
        if not isinstance(value, str):
            return ""
        words = value.strip().split()
        return " ".join(words[:_MAX_STEP_LABEL_WORDS])
