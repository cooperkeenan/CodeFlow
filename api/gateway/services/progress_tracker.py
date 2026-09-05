_STAGES = ["profiler", "tracer", "render"]


class ProgressTracker:
    def __init__(self) -> None:
        self.completed: int = 0
        self.active: bool = False
        self.error: str | None = None
        self.detail: str = ""
        self.substep: int = 0
        self.substeps: int = 0

    def start(self) -> None:
        self.completed = 0
        self.active = True
        self.error = None
        self.detail = ""
        self.substep = 0
        self.substeps = 0

    def complete(self, stage: str) -> None:
        if stage not in _STAGES:
            return
        self.completed = _STAGES.index(stage) + 1
        self.detail = ""
        self.substep = 0
        self.substeps = 0
        if self.completed >= len(_STAGES):
            self.active = False

    def track(self, detail: str, substep: int, substeps: int) -> None:
        self.detail = detail
        self.substep = substep
        self.substeps = substeps

    def fail(self, message: str) -> None:
        self.active = False
        self.error = message

    def snapshot(self) -> dict:
        total = len(_STAGES)
        current = _STAGES[self.completed] if self.completed < total else "done"
        return {
            "active": self.active,
            "completed": self.completed,
            "total": total,
            "percent": self._percent(total),
            "current": current,
            "detail": self.detail,
            "substep": self.substep,
            "substeps": self.substeps,
            "stages": list(_STAGES),
            "error": self.error,
        }

    def _percent(self, total: int) -> int:
        fraction = self.substep / self.substeps if self.substeps else 0.0
        return round(min(self.completed + fraction, total) / total * 100)
