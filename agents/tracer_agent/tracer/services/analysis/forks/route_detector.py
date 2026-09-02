from tracer.models.sites import DispatchSite
from tracer.services.analysis.contracts import (
    DispatchDetectionContext,
    RouteFrameworkScanner,
)


class RouteDetector:
    def __init__(self, scanners: tuple[RouteFrameworkScanner, ...]) -> None:
        self._scanners = scanners

    def detect(self, context: DispatchDetectionContext) -> tuple[DispatchSite, ...]:
        sites: list[DispatchSite] = []
        for scanner in self._scanners:
            sites.extend(scanner.scan(context))
        return tuple(sites)
