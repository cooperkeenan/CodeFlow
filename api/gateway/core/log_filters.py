import logging

_MUTED_PATHS = ("/ci/progress",)


class AccessLogFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        message = record.getMessage()
        return not any(path in message for path in _MUTED_PATHS)
