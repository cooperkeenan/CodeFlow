from dataclasses import dataclass
from typing import Protocol

from models.call_site import CallSite
from models.dispatch_site import DispatchSite
from models.project_index import ProjectIndex


@dataclass(frozen=True)
class DispatchDetectionContext:
    index: ProjectIndex
    callsites: tuple[CallSite, ...]


class DispatchDetector(Protocol):
    def detect(self, context: DispatchDetectionContext) -> tuple[DispatchSite, ...]: ...
