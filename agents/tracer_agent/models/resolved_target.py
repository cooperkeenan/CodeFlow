from dataclasses import dataclass
from typing import Literal


@dataclass(frozen=True)
class ResolvedTarget:
    fqn: str
    confidence: Literal["resolved", "inferred"]
