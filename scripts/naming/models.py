from dataclasses import dataclass


@dataclass(frozen=True)
class Candidate:
    name: str
    domain: str
    origin: str
    rationale: str = ""


@dataclass(frozen=True)
class Signal:
    probe: str
    kind: str
    status: str
    detail: str = ""


@dataclass(frozen=True)
class CheckResult:
    candidate: Candidate
    domain_status: str
    prior_art_hits: int
    verdict: str
    signals: tuple[Signal, ...]
    checked_at: str


@dataclass(frozen=True)
class HttpResponse:
    status: int
    body: str
    error: str = ""


@dataclass(frozen=True)
class DnsAnswer:
    rcode: int
    answers: int
    ok: bool
    error: str = ""
