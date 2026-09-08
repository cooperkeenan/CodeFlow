from naming.models import Candidate
from naming.statuses import VERDICT_REJECT
from naming.store import NameStore

DEFAULT_MODIFIERS: tuple[tuple[str, str], ...] = (
    ("", "hq"),
    ("get", ""),
    ("use", ""),
    ("", "labs"),
)


class VariantSource:
    def __init__(
        self,
        store: NameStore,
        modifiers: tuple[tuple[str, str], ...] = DEFAULT_MODIFIERS,
        origins: tuple[str, ...] = ("seed",),
        pool_limit: int = 400,
    ) -> None:
        self._store = store
        self._modifiers = modifiers
        self._origins = origins
        self._pool_limit = pool_limit
        self._emitted: set[str] = set()

    @property
    def source_name(self) -> str:
        return "variant"

    def next_batch(self, size: int, seen: set[str]) -> list[Candidate]:
        batch: list[Candidate] = []
        for name, rationale in self._pool():
            if len(batch) >= size:
                break
            if name.lower() in seen or name.lower() in self._emitted:
                continue
            self._emitted.add(name.lower())
            batch.append(
                Candidate(
                    name=name,
                    domain=f"{name.lower()}.com",
                    origin=self.source_name,
                    rationale=rationale,
                )
            )
        return batch

    def _pool(self) -> list[tuple[str, str]]:
        rows = self._store.latest((VERDICT_REJECT,), self._pool_limit)
        bases = sorted(
            {(row["name"], row["rationale"]) for row in rows if row["origin"] in self._origins}
        )
        return [
            (self._variant(name, prefix, suffix), rationale)
            for name, rationale in bases
            for prefix, suffix in self._modifiers
        ]

    def _variant(self, name: str, prefix: str, suffix: str) -> str:
        head = f"{prefix.capitalize()}{name.capitalize()}"
        tail = suffix.upper() if suffix == "hq" else suffix.capitalize()
        return head + tail
