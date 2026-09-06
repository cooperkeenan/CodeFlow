from dataclasses import dataclass
from typing import Literal


@dataclass(frozen=True)
class EndpointLink:
    kind: Literal["endpoint", "helper"]
    target: str
    label: str
