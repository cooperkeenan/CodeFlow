import logging

from shared.run_log.event_log import EventLog

_SELF_PREFIX = "codeflow."


class EventLogHandler(logging.Handler):
    def __init__(self, sink: EventLog, stage: str = "", level: int = logging.WARNING) -> None:
        super().__init__(level)
        self._sink = sink
        self._stage = stage

    def emit(self, record: logging.LogRecord) -> None:
        if record.name.startswith(_SELF_PREFIX):
            return
        level = "error" if record.levelno >= logging.ERROR else "warn"
        self._sink.append(level, self._stage, record.getMessage())
