from models.dispatch_site import DispatchSite
from services.analysis.dispatch_detector import DispatchDetectionContext
from services.analysis.route_framework_scanner import RouteFrameworkScanner


class RouteDetector:
    def __init__(self, scanners: tuple[RouteFrameworkScanner, ...]) -> None:
        self._scanners = scanners

    def detect(self, context: DispatchDetectionContext) -> tuple[DispatchSite, ...]:
        sites: list[DispatchSite] = []
        for scanner in self._scanners:
            sites.extend(scanner.scan(context))
        return tuple(sites)
