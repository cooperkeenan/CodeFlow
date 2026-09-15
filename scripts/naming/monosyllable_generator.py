import random

from naming.domain_namer import DomainNamer
from naming.models import Candidate
from naming.syllables import (
    CODAS,
    MAX_SYLLABLE_LENGTH,
    MIN_SYLLABLE_LENGTH,
    ONSETS,
    PLAIN_NUCLEI,
    SIGNATURE_NUCLEI,
)

_RATIONALE = "one-syllable coinage: onset, vowel, coda"


class MonosyllableGenerator:
    def __init__(
        self,
        seed: int = 4099,
        namer: DomainNamer | None = None,
        onsets: tuple[str, ...] = ONSETS,
        codas: tuple[str, ...] = CODAS,
    ) -> None:
        self._namer = namer or DomainNamer()
        self._pool = self._build_pool(onsets, codas, seed)
        self._cursor = 0

    @property
    def source_name(self) -> str:
        return "monosyllable"

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
                    rationale=_RATIONALE,
                )
            )
        return batch

    def _build_pool(self, onsets: tuple[str, ...], codas: tuple[str, ...], seed: int) -> list[str]:
        shuffler = random.Random(seed)
        tiers = [
            self._tier(onsets, nuclei, codas, shuffler)
            for nuclei in (SIGNATURE_NUCLEI, PLAIN_NUCLEI)
        ]
        return [name for tier in tiers for name in tier]

    def _tier(
        self,
        onsets: tuple[str, ...],
        nuclei: tuple[str, ...],
        codas: tuple[str, ...],
        shuffler: random.Random,
    ) -> list[str]:
        tier = [
            (onset + nucleus + coda).capitalize()
            for onset in onsets
            for nucleus in nuclei
            for coda in codas
            if self._sayable(onset, nucleus, coda)
        ]
        shuffler.shuffle(tier)
        return tier

    def _sayable(self, onset: str, nucleus: str, coda: str) -> bool:
        word = onset + nucleus + coda
        if not MIN_SYLLABLE_LENGTH <= len(word) <= MAX_SYLLABLE_LENGTH:
            return False
        if onset == coda or onset[-1] == coda[0]:
            return False
        if len(onset) > 2 and len(coda) > 1:
            return False
        if len(onset) + len(coda) > 3 and len(nucleus) > 1:
            return False
        return onset[0] != coda[-1] or len(onset) > 1
