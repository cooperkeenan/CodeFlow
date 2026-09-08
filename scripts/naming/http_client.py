import json
import urllib.error
import urllib.request
from typing import Any

from naming.models import HttpResponse

_DEFAULT_AGENT = "codeflow-name-search/1.0 (+domain availability research)"


class HttpClient:
    def __init__(self, timeout_s: float = 12.0, user_agent: str = _DEFAULT_AGENT) -> None:
        self._timeout_s = timeout_s
        self._user_agent = user_agent

    def get(self, url: str, headers: dict[str, str] | None = None) -> HttpResponse:
        request = urllib.request.Request(url, method="GET")
        request.add_header("User-Agent", self._user_agent)
        for key, value in (headers or {}).items():
            request.add_header(key, value)
        try:
            with urllib.request.urlopen(request, timeout=self._timeout_s) as response:
                return HttpResponse(response.status, self._decode(response.read()))
        except urllib.error.HTTPError as error:
            return HttpResponse(error.code, self._decode(error.read()))
        except (urllib.error.URLError, OSError, ValueError) as error:
            return HttpResponse(0, "", f"{type(error).__name__}: {error}")

    def get_json(self, url: str, headers: dict[str, str] | None = None) -> tuple[HttpResponse, Any]:
        merged = {"Accept": "application/json"}
        merged.update(headers or {})
        response = self.get(url, merged)
        if response.status != 200:
            return response, None
        try:
            return response, json.loads(response.body)
        except ValueError as error:
            return HttpResponse(response.status, "", f"bad json: {error}"), None

    def _decode(self, payload: bytes) -> str:
        return payload.decode("utf-8", errors="replace")
