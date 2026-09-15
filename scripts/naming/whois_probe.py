from naming.models import Candidate, Signal
from naming.statuses import (
    DOMAIN_AVAILABLE,
    DOMAIN_TAKEN,
    DOMAIN_UNKNOWN,
    KIND_DOMAIN,
)
from naming.whois_client import WhoisClient

_FREE_MARKERS = (
    "no match for",
    "not found",
    "no data found",
    "no entries found",
    "domain not found",
    "status: free",
    "status: available",
)
_TAKEN_MARKERS = ("domain name:", "domain:", "registrar:", "creation date:", "registered on:")


class WhoisProbe:
    def __init__(self, client: WhoisClient) -> None:
        self._client = client

    @property
    def probe_name(self) -> str:
        return "whois"

    @property
    def kind(self) -> str:
        return KIND_DOMAIN

    def check(self, candidate: Candidate) -> Signal:
        tld = candidate.domain.rsplit(".", 1)[-1]
        server = self._client.server_for(tld)
        try:
            body = self._client.query(candidate.domain, server).lower()
        except OSError as error:
            return self._signal(DOMAIN_UNKNOWN, f"{server}: {type(error).__name__}: {error}")
        if any(marker in body for marker in _FREE_MARKERS):
            return self._signal(DOMAIN_AVAILABLE, f"{server} has no record")
        if any(marker in body for marker in _TAKEN_MARKERS):
            return self._signal(DOMAIN_TAKEN, f"{server} holds a record")
        return self._signal(DOMAIN_UNKNOWN, f"{server} gave an unrecognised response")

    def _signal(self, status: str, detail: str) -> Signal:
        return Signal(self.probe_name, KIND_DOMAIN, status, detail)
