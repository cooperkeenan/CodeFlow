import sqlite3
from pathlib import Path

from naming.models import CheckResult

_SCHEMA = (
    """
    CREATE TABLE IF NOT EXISTS candidates (
        name TEXT PRIMARY KEY,
        domain TEXT NOT NULL,
        origin TEXT NOT NULL,
        rationale TEXT NOT NULL DEFAULT '',
        first_seen TEXT NOT NULL
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS checks (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL REFERENCES candidates(name),
        checked_at TEXT NOT NULL,
        domain_status TEXT NOT NULL,
        prior_art_hits INTEGER NOT NULL,
        verdict TEXT NOT NULL
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS signals (
        check_id INTEGER NOT NULL REFERENCES checks(id),
        probe TEXT NOT NULL,
        kind TEXT NOT NULL,
        status TEXT NOT NULL,
        detail TEXT NOT NULL DEFAULT ''
    )
    """,
    "CREATE INDEX IF NOT EXISTS idx_checks_name ON checks(name)",
    "CREATE INDEX IF NOT EXISTS idx_checks_verdict ON checks(verdict)",
)

_LATEST = """
    SELECT c.name, c.domain, c.origin, c.rationale,
           k.verdict, k.domain_status, k.prior_art_hits, k.checked_at
    FROM candidates c
    JOIN checks k ON k.id = (
        SELECT id FROM checks WHERE name = c.name ORDER BY id DESC LIMIT 1
    )
"""


class NameStore:
    def __init__(self, path: Path) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        self._connection = sqlite3.connect(str(path))
        self._connection.row_factory = sqlite3.Row
        self._ensure_schema()

    def known_names(self) -> set[str]:
        rows = self._connection.execute("SELECT name FROM candidates").fetchall()
        return {row["name"].lower() for row in rows}

    def record(self, result: CheckResult) -> None:
        candidate = result.candidate
        with self._connection:
            self._connection.execute(
                "INSERT OR IGNORE INTO candidates VALUES (?, ?, ?, ?, ?)",
                (
                    candidate.name,
                    candidate.domain,
                    candidate.origin,
                    candidate.rationale,
                    result.checked_at,
                ),
            )
            cursor = self._connection.execute(
                "INSERT INTO checks (name, checked_at, domain_status, prior_art_hits, verdict)"
                " VALUES (?, ?, ?, ?, ?)",
                (
                    candidate.name,
                    result.checked_at,
                    result.domain_status,
                    result.prior_art_hits,
                    result.verdict,
                ),
            )
            self._connection.executemany(
                "INSERT INTO signals VALUES (?, ?, ?, ?, ?)",
                [
                    (cursor.lastrowid, s.probe, s.kind, s.status, s.detail)
                    for s in result.signals
                ],
            )

    def latest(self, verdicts: tuple[str, ...] = (), limit: int = 50) -> list[sqlite3.Row]:
        clause = ""
        params: list[object] = []
        if verdicts:
            clause = f" WHERE k.verdict IN ({','.join('?' * len(verdicts))})"
            params.extend(verdicts)
        params.append(limit)
        query = f"{_LATEST}{clause} ORDER BY k.prior_art_hits ASC, c.name ASC LIMIT ?"
        return self._connection.execute(query, params).fetchall()

    def verdict_counts(self) -> dict[str, int]:
        query = f"SELECT k.verdict AS verdict, COUNT(*) AS total FROM ({_LATEST}) k GROUP BY k.verdict"
        return {row["verdict"]: row["total"] for row in self._connection.execute(query)}

    def signals_for(self, name: str) -> list[sqlite3.Row]:
        return self._connection.execute(
            "SELECT s.probe, s.kind, s.status, s.detail FROM signals s"
            " JOIN checks k ON k.id = s.check_id WHERE k.name = ?"
            " ORDER BY k.id DESC, s.rowid ASC LIMIT 16",
            (name,),
        ).fetchall()

    def close(self) -> None:
        self._connection.close()

    def _ensure_schema(self) -> None:
        with self._connection:
            for statement in _SCHEMA:
                self._connection.execute(statement)
