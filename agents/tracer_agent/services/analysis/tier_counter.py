from collections import Counter


class TierCounter:
    def __init__(self) -> None:
        self._counts: Counter[int] = Counter()
        self._ext_counts: Counter[int] = Counter()

    def record(self, tier: int, is_ext: bool = False) -> None:
        self._counts[tier] += 1
        if is_ext:
            self._ext_counts[tier] += 1

    @property
    def counts(self) -> dict[int, int]:
        return dict(sorted(self._counts.items()))

    @property
    def ext_counts(self) -> dict[int, int]:
        return dict(sorted(self._ext_counts.items()))
