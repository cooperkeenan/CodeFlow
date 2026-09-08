from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone

from naming.contracts import Probe
from naming.models import Candidate, CheckResult, Signal
from naming.verdict import VerdictAggregator


class CandidateProber:
    def __init__(
        self,
        probes: tuple[Probe, ...],
        aggregator: VerdictAggregator,
        workers: int = 4,
    ) -> None:
        self._probes = probes
        self._aggregator = aggregator
        self._workers = max(1, workers)

    def check(self, candidate: Candidate) -> CheckResult:
        signals = tuple(self._run(probe, candidate) for probe in self._probes)
        domain_status, hits, verdict = self._aggregator.assess(signals)
        return CheckResult(
            candidate=candidate,
            domain_status=domain_status,
            prior_art_hits=hits,
            verdict=verdict,
            signals=signals,
            checked_at=datetime.now(timezone.utc).isoformat(timespec="seconds"),
        )

    def check_many(self, candidates: list[Candidate]) -> list[CheckResult]:
        if not candidates:
            return []
        with ThreadPoolExecutor(max_workers=self._workers) as pool:
            return list(pool.map(self.check, candidates))

    def _run(self, probe: Probe, candidate: Candidate) -> Signal:
        try:
            return probe.check(candidate)
        except Exception as error:
            return Signal(probe.probe_name, probe.kind, "unknown", f"probe failed: {error}")
