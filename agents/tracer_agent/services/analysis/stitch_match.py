from dataclasses import dataclass

from shared.models.flow_graph import Confidence


@dataclass(frozen=True)
class StitchMatch:
    entry_id: str
    confidence: Confidence
