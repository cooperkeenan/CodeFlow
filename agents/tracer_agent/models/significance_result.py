from collections.abc import Mapping
from dataclasses import dataclass

from models.site_verdict import SiteVerdict


@dataclass(frozen=True)
class SignificanceResult:
    utilities: frozenset[str]
    verdicts: Mapping[str, SiteVerdict]
    ranked_decisions: tuple[str, ...]
