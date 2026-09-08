from naming.models import Candidate
from naming.seed_names import SEED_NAMES


class SeedSource:
    def __init__(self, entries: tuple[tuple[str, str], ...] = SEED_NAMES) -> None:
        self._entries = entries
        self._cursor = 0

    @property
    def source_name(self) -> str:
        return "seed"

    def next_batch(self, size: int, seen: set[str]) -> list[Candidate]:
        batch: list[Candidate] = []
        while self._cursor < len(self._entries) and len(batch) < size:
            name, rationale = self._entries[self._cursor]
            self._cursor += 1
            if name.lower() in seen:
                continue
            batch.append(
                Candidate(
                    name=name,
                    domain=f"{name.lower()}.com",
                    origin=self.source_name,
                    rationale=rationale,
                )
            )
        return batch
