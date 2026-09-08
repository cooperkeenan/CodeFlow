import logging
import sys

from shared.run_log.event_log import EventLog

_GREY = "\x1b[90m"
_BOLD = "\x1b[97;1m"
_GREEN = "\x1b[32m"
_YELLOW = "\x1b[33m"
_RED = "\x1b[31m"
_RESET = "\x1b[0m"


class Console:
    def __init__(
        self,
        logger: logging.Logger,
        sink: EventLog | None = None,
        colour: bool | None = None,
    ) -> None:
        self._logger = logger
        self._sink = sink
        self._stage = ""
        self._colour = bool(getattr(sys.stdout, "isatty", lambda: False)()) if colour is None else colour

    def stage(self, index: int, total: int, key: str, title: str) -> None:
        self._stage = key
        self._logger.info(self._paint(f"[{index}/{total}] {title}", _BOLD))
        self._record("stage", title)

    def step(self, text: str) -> None:
        self._logger.info(self._paint(f"       {text}", _GREY))
        self._record("step", text)

    def done(self, text: str) -> None:
        self._logger.info(self._paint(f"    OK {text}", _GREEN))
        self._record("done", text)

    def warn(self, text: str) -> None:
        self._logger.warning(self._paint(f"  WARN {text}", _YELLOW))
        self._record("warn", text)

    def failed(self, text: str) -> None:
        self._logger.error(self._paint(f"  FAIL {text}", _RED))
        self._record("error", text)

    def adopt(self, level: str, stage: str, message: str, ts: float) -> None:
        if self._sink is not None:
            self._sink.adopt(level, stage, message, ts)

    def _record(self, level: str, message: str) -> None:
        if self._sink is not None:
            self._sink.append(level, self._stage, message)

    def _paint(self, text: str, colour: str) -> str:
        return f"{colour}{text}{_RESET}" if self._colour else text
