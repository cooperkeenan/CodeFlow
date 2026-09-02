from typing import Protocol

from tracer.models.sites import DispatchSite
from tracer.services.analysis.contracts import DispatchDetectionContext


class DispatchDetector(Protocol):
    def detect(self, context: DispatchDetectionContext) -> tuple[DispatchSite, ...]: ...
