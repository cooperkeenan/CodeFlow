import time

from naming.contracts import CandidateSource
from naming.models import Candidate
from naming.prober import CandidateProber
from naming.reporter import ConsoleReporter
from naming.store import NameStore


class NameSearchPipeline:
    def __init__(
        self,
        sources: tuple[CandidateSource, ...],
        prober: CandidateProber,
        store: NameStore,
        reporter: ConsoleReporter,
        db_label: str,
        batch_size: int = 8,
        pause_s: float = 0.0,
    ) -> None:
        self._sources = sources
        self._prober = prober
        self._store = store
        self._reporter = reporter
        self._db_label = db_label
        self._batch_size = max(1, batch_size)
        self._pause_s = pause_s

    def run(self, rounds: int) -> int:
        seen = self._store.known_names()
        checked = 0
        for index in range(1, rounds + 1):
            batch = self._next_batch(seen)
            if not batch:
                self._reporter.exhausted()
                break
            self._reporter.round_start(index, rounds, len(batch))
            checked += self._check_batch(batch)
            seen.update(candidate.name.lower() for candidate in batch)
            if self._pause_s and index < rounds:
                time.sleep(self._pause_s)
        self._reporter.summary(self._store.verdict_counts(), self._db_label)
        return checked

    def check_names(self, names: list[str]) -> int:
        batch = [
            Candidate(name=name, domain=f"{name.lower()}.com", origin="manual")
            for name in names
        ]
        self._reporter.round_start(1, 1, len(batch))
        checked = self._check_batch(batch)
        self._reporter.summary(self._store.verdict_counts(), self._db_label)
        return checked

    def _check_batch(self, batch: list[Candidate]) -> int:
        results = self._prober.check_many(batch)
        for result in results:
            self._store.record(result)
            self._reporter.result(result)
        return len(results)

    def _next_batch(self, seen: set[str]) -> list[Candidate]:
        batch: list[Candidate] = []
        for source in self._sources:
            if len(batch) >= self._batch_size:
                break
            batch.extend(source.next_batch(self._batch_size - len(batch), seen))
        return batch
