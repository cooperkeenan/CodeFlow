import logging
import sys

_GREY = "\x1b[90m"
_YELLOW = "\x1b[33m"
_RED = "\x1b[31m"
_RESET = "\x1b[0m"

_LEVEL_COLOURS = {
    logging.WARNING: _YELLOW,
    logging.ERROR: _RED,
    logging.CRITICAL: _RED,
}


class RunFormatter(logging.Formatter):
    def __init__(self, service: str, colour: bool | None = None) -> None:
        super().__init__(datefmt="%H:%M:%S")
        self._service = service
        self._colour = bool(getattr(sys.stdout, "isatty", lambda: False)()) if colour is None else colour

    def format(self, record: logging.LogRecord) -> str:
        prefix = f"{self.formatTime(record, self.datefmt)} {self._service:<8}"
        if self._colour:
            prefix = f"{_GREY}{prefix}{_RESET}"
        body = record.getMessage()
        colour = _LEVEL_COLOURS.get(record.levelno)
        if colour and self._colour and "\x1b[" not in body:
            body = f"{colour}{body}{_RESET}"
        if record.exc_info:
            body = f"{body}\n{self.formatException(record.exc_info)}"
        return f"{prefix} {body}"
