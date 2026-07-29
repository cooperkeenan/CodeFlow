from typing import Protocol

from models.dispatch_site import DispatchSite
from services.analysis.dispatch_detector import DispatchDetectionContext


class RouteFrameworkScanner(Protocol):
    def scan(self, context: DispatchDetectionContext) -> tuple[DispatchSite, ...]: ...
