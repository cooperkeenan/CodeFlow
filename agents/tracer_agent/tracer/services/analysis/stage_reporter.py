import logging
import time

from tracer.services.analysis.stage_names import STAGE_NAMES, label_for

from shared.run_log.console import Console
from shared.run_log.event_log import EventLog

logger = logging.getLogger("codeflow.trace")


class StageReporter:
    def __init__(self) -> None:
        self._events = EventLog()
        self._console = Console(logger, self._events)
        self._current = ""
        self._detail = ""
        self._index = 0
        self._stage_started = 0.0
        self._run_started = 0.0
        self._active = False

    def start(self, repo: str) -> None:
        self._active = True
        self._index = 0
        self._current = ""
        self._detail = ""
        self._run_started = time.monotonic()
        self._stage_started = self._run_started
        self._events.clear()
        self._console.stage(0, len(STAGE_NAMES), "start", f"tracing {repo} — {len(STAGE_NAMES)} stages")

    def ensure_started(self, repo: str) -> None:
        if not self._active:
            self.start(repo)

    def begin(self, name: str, detail: str = "") -> None:
        self._close()
        self._current = name
        self._detail = detail
        self._index = STAGE_NAMES.index(name) + 1 if name in STAGE_NAMES else self._index
        self._stage_started = time.monotonic()
        title = f"{label_for(name)}{f' — {detail}' if detail else ''}"
        self._console.stage(self._index, len(STAGE_NAMES), name, title)

    def note(self, detail: str) -> None:
        self._detail = detail
        self._console.step(detail)

    def warn(self, detail: str) -> None:
        self._console.warn(detail)

    def finish(self, detail: str = "") -> None:
        self._close(detail)
        self._active = False
        self._console.done(f"trace complete in {time.monotonic() - self._run_started:.1f}s")

    def fail(self, message: str) -> None:
        self._active = False
        self._console.failed(f"{self._current or 'trace'} — {message}")

    @property
    def sink(self) -> EventLog:
        return self._events

    def snapshot(self, since: int = 0) -> dict:
        return {
            "active": self._active,
            "stage": self._current,
            "stage_label": label_for(self._current),
            "detail": self._detail,
            "completed": self._index,
            "total": len(STAGE_NAMES),
            "stages": list(STAGE_NAMES),
            "labels": [label_for(name) for name in STAGE_NAMES],
            "events": [event.as_dict() for event in self._events.since(since)],
            "event_seq": self._events.latest_seq(),
            "elapsed": round(time.monotonic() - self._run_started, 1) if self._active else 0.0,
        }

    def _close(self, detail: str = "") -> None:
        if not self._current:
            return
        elapsed = time.monotonic() - self._stage_started
        suffix = detail or self._detail
        self._console.done(
            f"{label_for(self._current)} in {elapsed:.1f}s{f' ({suffix})' if suffix else ''}"
        )
