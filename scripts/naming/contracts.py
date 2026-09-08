from typing import Protocol

from naming.models import Candidate, Signal


class Probe(Protocol):
    @property
    def probe_name(self) -> str: ...

    @property
    def kind(self) -> str: ...

    def check(self, candidate: Candidate) -> Signal: ...


class CandidateSource(Protocol):
    @property
    def source_name(self) -> str: ...

    def next_batch(self, size: int, seen: set[str]) -> list[Candidate]: ...
