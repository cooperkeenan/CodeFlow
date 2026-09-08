from naming.http_client import HttpClient
from naming.models import Candidate, Signal
from naming.statuses import (
    DOMAIN_AVAILABLE,
    DOMAIN_TAKEN,
    DOMAIN_UNKNOWN,
    KIND_DOMAIN,
)

VERISIGN_COM_RDAP = "https://rdap.verisign.com/com/v1/domain/"
BOOTSTRAP_RDAP = "https://rdap.org/domain/"


class RdapProbe:
    def __init__(self, http: HttpClient, base_url: str = VERISIGN_COM_RDAP) -> None:
        self._http = http
        self._base_url = base_url

    @property
    def probe_name(self) -> str:
        return "rdap"

    @property
    def kind(self) -> str:
        return KIND_DOMAIN

    def check(self, candidate: Candidate) -> Signal:
        response = self._http.get(
            self._base_url + candidate.domain, {"Accept": "application/rdap+json"}
        )
        if response.status == 200:
            return self._signal(DOMAIN_TAKEN, "registry holds a record")
        if response.status == 404:
            return self._signal(DOMAIN_AVAILABLE, "registry has no record")
        if response.status == 0:
            return self._signal(DOMAIN_UNKNOWN, f"unreachable: {response.error}")
        return self._signal(DOMAIN_UNKNOWN, f"http {response.status}")

    def _signal(self, status: str, detail: str) -> Signal:
        return Signal(self.probe_name, KIND_DOMAIN, status, detail)
