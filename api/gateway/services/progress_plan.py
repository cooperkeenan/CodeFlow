from dataclasses import dataclass

TRACER_KEY = "tracer"


@dataclass(frozen=True)
class ProgressStage:
    key: str
    label: str
    detail: str
    weight: int


STAGES: tuple[ProgressStage, ...] = (
    ProgressStage("profiler", "Profile", "Reading the repo layout and zones", 15),
    ProgressStage(TRACER_KEY, "Trace", "Indexing code and judging decisions", 60),
    ProgressStage("render", "Render", "Placing nodes and edges", 15),
    ProgressStage("save", "Save", "Writing the repo map to the database", 10),
)


class StagePlan:
    def __init__(self, stages: tuple[ProgressStage, ...] = STAGES) -> None:
        self._stages = stages
        self._total_weight = sum(stage.weight for stage in stages) or 1

    @property
    def stages(self) -> tuple[ProgressStage, ...]:
        return self._stages

    @property
    def count(self) -> int:
        return len(self._stages)

    def index_of(self, key: str) -> int:
        return next((i for i, stage in enumerate(self._stages) if stage.key == key), -1)

    def stage_at(self, index: int) -> ProgressStage | None:
        return self._stages[index] if 0 <= index < len(self._stages) else None

    def percent(self, completed: int, fraction: float) -> int:
        done_weight = sum(stage.weight for stage in self._stages[:completed])
        current = self.stage_at(completed)
        partial = current.weight * max(0.0, min(fraction, 1.0)) if current else 0
        return round(min(done_weight + partial, self._total_weight) / self._total_weight * 100)

    def points(self, completed: int, sub_labels: list[str], sub_done: int) -> list[dict]:
        points: list[dict] = []
        offset = 0
        for index, stage in enumerate(self._stages):
            state = self._state(index, completed)
            if stage.key != TRACER_KEY or not sub_labels:
                points.append({
                    "key": stage.key, "label": stage.label, "phase": stage.key,
                    "state": state, "at": self._at(offset),
                })
            else:
                points.extend(self._sub_points(stage, sub_labels, state, sub_done, offset))
            offset += stage.weight
        return points

    def _sub_points(
        self, stage: ProgressStage, sub_labels: list[str],
        state: str, sub_done: int, offset: int,
    ) -> list[dict]:
        share = stage.weight / len(sub_labels)
        return [
            {
                "key": f"{stage.key}:{label}",
                "label": label,
                "phase": stage.key,
                "state": state if state != "active" else self._state(index, sub_done),
                "at": self._at(offset + share * index),
            }
            for index, label in enumerate(sub_labels)
        ]

    def _at(self, weight: float) -> int:
        return round(weight / self._total_weight * 100)

    @staticmethod
    def _state(index: int, completed: int) -> str:
        if index < completed:
            return "done"
        return "active" if index == completed else "pending"
