from naming.dns_resolver import RECORD_A, RECORD_NS, DnsResolver
from naming.models import Candidate, Signal
from naming.statuses import (
    DOMAIN_LIKELY_AVAILABLE,
    DOMAIN_TAKEN,
    DOMAIN_UNKNOWN,
    KIND_DOMAIN,
)

_NXDOMAIN = 3


class DnsProbe:
    def __init__(self, resolver: DnsResolver) -> None:
        self._resolver = resolver

    @property
    def probe_name(self) -> str:
        return "dns"

    @property
    def kind(self) -> str:
        return KIND_DOMAIN

    def check(self, candidate: Candidate) -> Signal:
        nameservers = self._resolver.query(candidate.domain, RECORD_NS)
        if not nameservers.ok:
            return self._signal(DOMAIN_UNKNOWN, nameservers.error)
        if nameservers.rcode == _NXDOMAIN:
            return self._signal(DOMAIN_LIKELY_AVAILABLE, "NXDOMAIN, no delegation")
        if nameservers.rcode == 0 and nameservers.answers:
            return self._signal(DOMAIN_TAKEN, f"{nameservers.answers} NS record(s)")
        addresses = self._resolver.query(candidate.domain, RECORD_A)
        if addresses.ok and addresses.rcode == 0 and addresses.answers:
            return self._signal(DOMAIN_TAKEN, f"{addresses.answers} A record(s)")
        return self._signal(DOMAIN_UNKNOWN, f"rcode={nameservers.rcode}, no records")

    def _signal(self, status: str, detail: str) -> Signal:
        return Signal(self.probe_name, KIND_DOMAIN, status, detail)
