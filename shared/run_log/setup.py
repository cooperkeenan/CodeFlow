import logging
import sys

from shared.run_log.formatter import RunFormatter

_QUIET_LOGGERS = ("httpx", "httpcore", "urllib3", "anthropic", "asyncio")


def configure_logging(service: str, level: int = logging.INFO) -> None:
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(RunFormatter(service))
    root = logging.getLogger()
    root.handlers = [handler]
    root.setLevel(level)
    for name in _QUIET_LOGGERS:
        logging.getLogger(name).setLevel(logging.WARNING)
