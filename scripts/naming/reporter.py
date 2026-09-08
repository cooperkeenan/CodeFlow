from naming.models import CheckResult
from naming.statuses import VERDICT_ORDER

_MARKS = {
    "strong": "STRONG",
    "check": "CHECK ",
    "unknown": "UNSURE",
    "reject": "TAKEN ",
}


class ConsoleReporter:
    def __init__(self, verbose: bool = False) -> None:
        self._verbose = verbose

    def round_start(self, index: int, total: int, size: int) -> None:
        print(f"\n-- round {index}/{total}: checking {size} candidate(s)")

    def result(self, result: CheckResult) -> None:
        mark = _MARKS.get(result.verdict, result.verdict)
        line = f"  [{mark}] {result.candidate.domain:<22} {result.domain_status}"
        if result.prior_art_hits:
            line += f", prior art x{result.prior_art_hits}"
        print(line)
        if self._verbose:
            for signal in result.signals:
                print(f"           {signal.probe:<8} {signal.status:<17} {signal.detail}")

    def exhausted(self) -> None:
        print("\nno unchecked candidates left; add seeds or widen the word banks")

    def summary(self, counts: dict[str, int], db_path: str) -> None:
        print("\ntotals by latest verdict:")
        for verdict in VERDICT_ORDER:
            print(f"  {verdict:<9} {counts.get(verdict, 0)}")
        print(f"stored in {db_path}")
