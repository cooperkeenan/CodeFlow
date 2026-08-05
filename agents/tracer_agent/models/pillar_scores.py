from collections.abc import Mapping
from dataclasses import dataclass


@dataclass(frozen=True)
class PillarScores:
    hub: Mapping[str, float]
    authority: Mapping[str, float]

    def score(self, component: str | None) -> float:
        if component is None:
            return 0.0
        return self.hub.get(component, 0.0)

    def role(self, component: str | None) -> str:
        if component is None:
            return "authority"
        if self.hub.get(component, 0.0) >= self.authority.get(component, 0.0):
            return "hub"
        return "authority"
