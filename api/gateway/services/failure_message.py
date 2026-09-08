import httpx

_BODY_LIMIT = 300


def describe_failure(exc: BaseException) -> str:
    if isinstance(exc, httpx.HTTPStatusError):
        return _from_status_error(exc)
    if isinstance(exc, httpx.TimeoutException):
        return f"{exc.request.url.host} timed out — the agent took too long to answer"
    if isinstance(exc, httpx.ConnectError):
        return f"could not reach {exc.request.url.host}:{exc.request.url.port} — is the agent running?"
    detail = getattr(exc, "detail", None)
    if detail:
        return str(detail)
    message = str(exc).strip()
    return f"{type(exc).__name__}: {message}" if message else type(exc).__name__


def _from_status_error(exc: httpx.HTTPStatusError) -> str:
    body = exc.response.text.strip().replace("\n", " ")
    suffix = f" — {body[:_BODY_LIMIT]}" if body else ""
    return f"{exc.request.url.path} returned {exc.response.status_code}{suffix}"
