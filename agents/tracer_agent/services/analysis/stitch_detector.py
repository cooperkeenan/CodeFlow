from typing import Protocol

from models.effect_site import EffectSite
from models.flow_entry import FlowEntry
from shared.models.flow_graph import FlowEdge


class StitchDetector(Protocol):
    def detect(
        self, effects: tuple[EffectSite, ...], entries: tuple[FlowEntry, ...]
    ) -> tuple[FlowEdge, ...]: ...
