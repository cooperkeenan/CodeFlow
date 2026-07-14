_STAGES = ["profiler", "tracer", "layout", "render"]


class ProgressTracker:
    def __init__(self) -> None:
        self.completed: int = 0
        self.active: bool = False
        self.error: str | None = None

    def start(self) -> None:
        self.completed = 0
        self.active = True
        self.error = None

    def complete(self, stage: str) -> None:
        if stage not in _STAGES:
            return
        self.completed = _STAGES.index(stage) + 1
        if self.completed >= len(_STAGES):
            self.active = False

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
            "percent": round(self.completed / total * 100),
            "current": current,
            "stages": list(_STAGES),
            "error": self.error,
        }
