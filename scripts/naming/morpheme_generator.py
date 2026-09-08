import random

from naming.models import Candidate
from naming.morphemes import MAX_NAME_LENGTH, ROOTS, SUFFIXES


class MorphemeGenerator:
    def __init__(
        self,
        roots: tuple[str, ...] = ROOTS,
        suffixes: tuple[str, ...] = SUFFIXES,
        seed: int = 1729,
    ) -> None:
        self._pool = self._build_pool(roots, suffixes, seed)
        self._cursor = 0

    @property
    def source_name(self) -> str:
        return "morpheme"

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
                    domain=f"{name.lower()}.com",
                    origin=self.source_name,
                    rationale="generated from the structure and clarity word banks",
                )
            )
        return batch

    def _build_pool(
        self, roots: tuple[str, ...], suffixes: tuple[str, ...], seed: int
    ) -> list[str]:
        pool = [
            (root + suffix).capitalize()
            for root in sorted(roots)
            for suffix in sorted(suffixes)
            if self._readable(root, suffix)
        ]
        random.Random(seed).shuffle(pool)
        return pool

    def _readable(self, root: str, suffix: str) -> bool:
        joined = root + suffix
        if root == suffix or len(joined) > MAX_NAME_LENGTH:
            return False
        if root[-1] == suffix[0]:
            return False
        return root not in suffix and suffix not in root
