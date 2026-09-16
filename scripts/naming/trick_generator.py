import re
from itertools import combinations

from naming.codeflow_words import CODEFLOW_WORDS
from naming.domain_namer import DomainNamer
from naming.models import Candidate
from naming.tricks import (
    MAX_TRICK_LENGTH,
    MAX_TRICKS_PER_WORD,
    MIN_TRICK_LENGTH,
    TRICKS,
    Trick,
)


class TrickGenerator:
    def __init__(
        self,
        words: tuple[tuple[str, str], ...] = CODEFLOW_WORDS,
        tricks: tuple[Trick, ...] = TRICKS,
        namer: DomainNamer | None = None,
        max_tricks: int = MAX_TRICKS_PER_WORD,
    ) -> None:
        self._namer = namer or DomainNamer()
        self._pool = self._build_pool(words, tricks, max_tricks)
        self._cursor = 0

    @property
    def source_name(self) -> str:
        return "trick"

    def next_batch(self, size: int, seen: set[str]) -> list[Candidate]:
        batch: list[Candidate] = []
        while self._cursor < len(self._pool) and len(batch) < size:
            name, source, applied = self._pool[self._cursor]
            self._cursor += 1
            if name.lower() in seen:
                continue
            batch.append(
                Candidate(
                    name=name.capitalize(),
                    domain=self._namer.domain_for(name),
                    origin=self.source_name,
                    rationale=f"{source} via {applied}",
                )
            )
        return batch

    def _build_pool(
        self,
        words: tuple[tuple[str, str], ...],
        tricks: tuple[Trick, ...],
        max_tricks: int,
    ) -> list[tuple[str, str, str]]:
        best: dict[str, tuple[int, int, str, str]] = {}
        for order, (word, _note) in enumerate(words):
            for depth in range(1, max_tricks + 1):
                for combo in combinations(tricks, depth):
                    twisted = self._apply(word, combo)
                    if twisted is None:
                        continue
                    applied = " + ".join(trick.name for trick in combo)
                    key = (depth, order, word, applied)
                    if twisted not in best or key < best[twisted]:
                        best[twisted] = key
        ranked = sorted(best, key=lambda name: best[name])
        return [(name, best[name][2], best[name][3]) for name in ranked]

    def _apply(self, word: str, combo: tuple[Trick, ...]) -> str | None:
        current = word
        for trick in combo:
            current = re.sub(trick.pattern, trick.replacement, current)
        if current == word or not MIN_TRICK_LENGTH <= len(current) <= MAX_TRICK_LENGTH:
            return None
        if not current.isalpha() or not re.search(r"[aeiouy]", current):
            return None
        return current
