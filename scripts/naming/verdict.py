from naming.models import Signal
from naming.statuses import (
    DOMAIN_FREE_STATUSES,
    DOMAIN_TAKEN,
    DOMAIN_UNKNOWN,
    KIND_DOMAIN,
    PRIOR_ART_HIT,
    VERDICT_CHECK,
    VERDICT_REJECT,
    VERDICT_STRONG,
    VERDICT_UNKNOWN,
)

_DEFAULT_AUTHORITY = ("rdap", "dns")


class VerdictAggregator:
    def __init__(self, authority: tuple[str, ...] = _DEFAULT_AUTHORITY) -> None:
        self._authority = authority

    def assess(self, signals: tuple[Signal, ...]) -> tuple[str, int, str]:
        domain_status = self._domain_status(signals)
        hits = sum(1 for signal in signals if signal.status == PRIOR_ART_HIT)
        return domain_status, hits, self._verdict(domain_status, hits)

    def _domain_status(self, signals: tuple[Signal, ...]) -> str:
        by_probe = {
            signal.probe: signal.status for signal in signals if signal.kind == KIND_DOMAIN
        }
        for probe in self._authority:
            status = by_probe.get(probe, DOMAIN_UNKNOWN)
            if status != DOMAIN_UNKNOWN:
                return status
        return DOMAIN_UNKNOWN

    def _verdict(self, domain_status: str, hits: int) -> str:
        if domain_status == DOMAIN_TAKEN:
            return VERDICT_REJECT
        if domain_status not in DOMAIN_FREE_STATUSES:
            return VERDICT_UNKNOWN
        return VERDICT_STRONG if hits == 0 else VERDICT_CHECK
