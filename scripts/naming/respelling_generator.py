from itertools import product

from naming.domain_namer import DomainNamer
from naming.models import Candidate
from naming.respellings import GRAPHEMES, MAX_RESPELLING_LENGTH


class RespellingGenerator:
    def __init__(
        self,
        word: str,
        sounds: tuple[str, ...],
        namer: DomainNamer | None = None,
    ) -> None:
        self._word = word.lower()
        self._namer = namer or DomainNamer()
        self._pool = self._build_pool(sounds)
        self._cursor = 0

    @property
    def source_name(self) -> str:
        return "respelling"

    def next_batch(self, size: int, seen: set[str]) -> list[Candidate]:
        batch: list[Candidate] = []
        while self._cursor < len(self._pool) and len(batch) < size:
            name = self._pool[self._cursor]
            self._cursor += 1
            if name.lower() in seen:
                continue
            batch.append(
                Candidate(
                    name=name,
                    domain=self._namer.domain_for(name),
                    origin=self.source_name,
                    rationale=f"sounds like '{self._word}', spelled differently",
                )
            )
        return batch

    def _build_pool(self, sounds: tuple[str, ...]) -> list[str]:
        options = [GRAPHEMES[sound] for sound in sounds]
        scored: dict[str, int] = {}
        for choice in product(*options):
            spelling = "".join(choice)
            if spelling == self._word or len(spelling) > MAX_RESPELLING_LENGTH:
                continue
            drift = sum(options[i].index(part) for i, part in enumerate(choice))
            if spelling not in scored or drift < scored[spelling]:
                scored[spelling] = drift
        ranked = sorted(scored, key=lambda s: (scored[s], len(s), s))
        return [spelling.capitalize() for spelling in ranked]
