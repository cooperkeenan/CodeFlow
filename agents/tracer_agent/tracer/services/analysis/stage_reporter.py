import logging
import time

logger = logging.getLogger(__name__)

STAGE_NAMES = [
    "index",
    "resolve",
    "forks",
    "effects",
    "judge",
    "condense",
    "entries",
    "stitch",
    "rank",
    "budget",
    "name",
    "review",
    "symbols",
]


class StageReporter:
    def __init__(self) -> None:
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
        logger.info("[trace] %s: %d stages", repo, len(STAGE_NAMES))

    def begin(self, name: str, detail: str = "") -> None:
        self._close()
        self._current = name
        self._detail = detail
        self._index = STAGE_NAMES.index(name) + 1 if name in STAGE_NAMES else self._index
        self._stage_started = time.monotonic()
        logger.info("[trace] %d/%d %s starting", self._index, len(STAGE_NAMES), name)

    def note(self, detail: str) -> None:
        self._detail = detail
        logger.info("[trace] %s: %s", self._current or "stage", detail)

    def finish(self, detail: str = "") -> None:
        self._close(detail)
        self._active = False
        logger.info("[trace] complete in %.1fs", time.monotonic() - self._run_started)

    def snapshot(self) -> dict:
        return {
            "active": self._active,
            "stage": self._current,
            "detail": self._detail,
            "completed": self._index,
            "total": len(STAGE_NAMES),
            "stages": list(STAGE_NAMES),
            "elapsed": round(time.monotonic() - self._run_started, 1) if self._active else 0.0,
        }

    def _close(self, detail: str = "") -> None:
        if not self._current:
            return
        elapsed = time.monotonic() - self._stage_started
        suffix = detail or self._detail
        logger.info(
            "[trace] %d/%d %s done in %.1fs%s",
            self._index,
            len(STAGE_NAMES),
            self._current,
            elapsed,
            f" ({suffix})" if suffix else "",
        )
