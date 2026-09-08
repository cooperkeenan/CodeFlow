import logging
import time

from gateway.services.progress_plan import TRACER_KEY, StagePlan

from shared.run_log.console import Console
from shared.run_log.event_log import EventLog

logger = logging.getLogger("codeflow.run")


class ProgressTracker:
    def __init__(self, plan: StagePlan | None = None) -> None:
        self._plan = plan or StagePlan()
        self._events = EventLog()
        self._console = Console(logger, self._events)
        self._reset()

    def start(self, repo: str = "") -> None:
        self._reset()
        self._repo = repo
        self._active = True
        self._started = time.monotonic()
        self._events.clear()
        if repo:
            self._console.stage(0, self._plan.count, "start", f"analysing {repo}")

    def begin(self, stage: str, detail: str = "") -> None:
        index = self._plan.index_of(stage)
        if index < 0:
            return
        self._completed = index
        self._active = True
        self._substep = 0
        self._sub_labels = []
        definition = self._plan.stage_at(index)
        self._detail = detail or (definition.detail if definition else "")
        title = f"{stage} — {self._detail}" if self._detail else stage
        self._console.stage(index + 1, self._plan.count, stage, title)

    def step(self, text: str) -> None:
        self._detail = text
        self._console.step(text)

    def warn(self, text: str) -> None:
        self._console.warn(text)

    def complete(self, stage: str, summary: str = "") -> None:
        index = self._plan.index_of(stage)
        if index < 0:
            return
        self._completed = index + 1
        self._detail = ""
        self._substep = 0
        self._sub_labels = []
        if summary:
            self._console.done(summary)
        if self._completed >= self._plan.count:
            self._active = False
            self._console.done(f"finished in {self.elapsed():.1f}s")

    def track(self, detail: str, substep: int, sub_labels: list[str]) -> None:
        self._detail = detail
        self._substep = substep
        if sub_labels:
            self._sub_labels = sub_labels

    def merge_events(self, events: list[dict]) -> None:
        for event in events:
            seq = int(event.get("seq", 0))
            if seq <= self._tracer_seq:
                continue
            self._tracer_seq = seq
            self._console.adopt(
                event.get("level", "step"),
                TRACER_KEY,
                event.get("message", ""),
                float(event.get("ts", time.time())),
            )

    def fail(self, message: str) -> None:
        self._active = False
        self._error = message
        stage = self._plan.stage_at(self._completed)
        self._failed_stage = stage.key if stage else "unknown"
        self._console.failed(f"{self._failed_stage} — {message}")

    @property
    def sink(self) -> EventLog:
        return self._events

    @property
    def active(self) -> bool:
        return self._active

    @property
    def current_stage(self) -> str:
        stage = self._plan.stage_at(self._completed)
        return stage.key if stage else "done"

    @property
    def tracer_seq(self) -> int:
        return self._tracer_seq

    def elapsed(self) -> float:
        return time.monotonic() - self._started if self._started else 0.0

    def snapshot(self, since: int = 0) -> dict:
        stage = self._plan.stage_at(self._completed)
        fraction = self._substep / len(self._sub_labels) if self._sub_labels else 0.0
        return {
            "active": self._active,
            "repo": self._repo,
            "completed": self._completed,
            "total": self._plan.count,
            "percent": self._plan.percent(self._completed, fraction),
            "percent_ceiling": self._plan.percent(self._completed, 1.0),
            "current": stage.key if stage else "done",
            "stage_label": stage.label if stage else "Done",
            "detail": self._detail,
            "substep": self._substep,
            "substeps": len(self._sub_labels),
            "stages": [item.key for item in self._plan.stages],
            "phases": [
                {"key": item.key, "label": item.label, "state": self._phase_state(item.key)}
                for item in self._plan.stages
            ],
            "points": self._plan.points(
                self._completed, self._sub_labels, max(self._substep - 1, 0)
            ),
            "events": [event.as_dict() for event in self._events.since(since)],
            "event_seq": self._events.latest_seq(),
            "elapsed": round(self.elapsed(), 1),
            "error": self._error,
            "failed_stage": self._failed_stage,
        }

    def _phase_state(self, key: str) -> str:
        index = self._plan.index_of(key)
        if index < self._completed:
            return "done"
        if index > self._completed:
            return "pending"
        return "failed" if self._error else "active"

    def _reset(self) -> None:
        self._repo = ""
        self._completed = 0
        self._active = False
        self._error: str | None = None
        self._failed_stage: str | None = None
        self._detail = ""
        self._substep = 0
        self._sub_labels: list[str] = []
        self._started = 0.0
        self._tracer_seq = 0
