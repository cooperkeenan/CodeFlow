from urllib.parse import quote_plus

from naming.http_client import HttpClient
from naming.models import Candidate, Signal
from naming.statuses import (
    KIND_PRIOR_ART,
    PRIOR_ART_CLEAR,
    PRIOR_ART_HIT,
    PRIOR_ART_UNKNOWN,
)

_SEARCH_URL = "https://api.github.com/search/repositories?q={query}&per_page=1"


class GithubRepoProbe:
    def __init__(self, http: HttpClient, token: str = "", min_stars: int = 25) -> None:
        self._http = http
        self._token = token
        self._min_stars = min_stars

    @property
    def probe_name(self) -> str:
        return "github"

    @property
    def kind(self) -> str:
        return KIND_PRIOR_ART

    def check(self, candidate: Candidate) -> Signal:
        query = quote_plus(f"{candidate.name.lower()} in:name stars:>={self._min_stars}")
        response, payload = self._http.get_json(_SEARCH_URL.format(query=query), self._headers())
        if response.status == 0:
            return self._signal(PRIOR_ART_UNKNOWN, f"unreachable: {response.error}")
        if response.status != 200 or not isinstance(payload, dict):
            return self._signal(PRIOR_ART_UNKNOWN, f"http {response.status}")
        total = int(payload.get("total_count", 0))
        if total:
            return self._signal(PRIOR_ART_HIT, f"{total} repo(s) named it, >={self._min_stars} stars")
        return self._signal(PRIOR_ART_CLEAR, f"no repo named it above {self._min_stars} stars")

    def _headers(self) -> dict[str, str]:
        headers = {"Accept": "application/vnd.github+json"}
        if self._token:
            headers["Authorization"] = f"Bearer {self._token}"
        return headers

    def _signal(self, status: str, detail: str) -> Signal:
        return Signal(self.probe_name, KIND_PRIOR_ART, status, detail)
