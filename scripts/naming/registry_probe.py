from naming.http_client import HttpClient
from naming.models import Candidate, Signal
from naming.statuses import (
    KIND_PRIOR_ART,
    PRIOR_ART_CLEAR,
    PRIOR_ART_HIT,
    PRIOR_ART_UNKNOWN,
)

PYPI_URL = "https://pypi.org/pypi/{name}/json"
NPM_URL = "https://registry.npmjs.org/{name}"


class PackageRegistryProbe:
    def __init__(self, registry: str, url_template: str, http: HttpClient) -> None:
        self._registry = registry
        self._url_template = url_template
        self._http = http

    @property
    def probe_name(self) -> str:
        return self._registry

    @property
    def kind(self) -> str:
        return KIND_PRIOR_ART

    def check(self, candidate: Candidate) -> Signal:
        url = self._url_template.format(name=candidate.name.lower())
        response = self._http.get(url)
        if response.status == 200:
            return self._signal(PRIOR_ART_HIT, f"package '{candidate.name.lower()}' exists")
        if response.status == 404:
            return self._signal(PRIOR_ART_CLEAR, "no package of that name")
        if response.status == 0:
            return self._signal(PRIOR_ART_UNKNOWN, f"unreachable: {response.error}")
        return self._signal(PRIOR_ART_UNKNOWN, f"http {response.status}")

    def _signal(self, status: str, detail: str) -> Signal:
        return Signal(self.probe_name, KIND_PRIOR_ART, status, detail)
