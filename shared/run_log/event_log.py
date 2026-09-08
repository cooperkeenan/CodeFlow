import time
from collections import deque

from shared.run_log.events import LogEvent

DEFAULT_CAPACITY = 500


class EventLog:
    def __init__(self, capacity: int = DEFAULT_CAPACITY) -> None:
        self._events: deque[LogEvent] = deque(maxlen=capacity)
        self._seq = 0

    def clear(self) -> None:
        self._events.clear()

    def append(self, level: str, stage: str, message: str) -> LogEvent:
        self._seq += 1
        event = LogEvent(seq=self._seq, ts=time.time(), level=level, stage=stage, message=message)
        self._events.append(event)
        return event

    def adopt(self, level: str, stage: str, message: str, ts: float) -> LogEvent:
        self._seq += 1
        event = LogEvent(seq=self._seq, ts=ts, level=level, stage=stage, message=message)
        self._events.append(event)
        return event

    def since(self, seq: int) -> list[LogEvent]:
        return [event for event in self._events if event.seq > seq]

    def tail(self, count: int) -> list[LogEvent]:
        return list(self._events)[-count:]

    def latest_seq(self) -> int:
        return self._seq
