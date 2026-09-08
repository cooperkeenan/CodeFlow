from dataclasses import dataclass

LEVELS = ("stage", "step", "done", "warn", "error")


@dataclass(frozen=True)
class LogEvent:
    seq: int
    ts: float
    level: str
    stage: str
    message: str

    def as_dict(self) -> dict:
        return {
            "seq": self.seq,
            "ts": self.ts,
            "level": self.level,
            "stage": self.stage,
            "message": self.message,
        }
