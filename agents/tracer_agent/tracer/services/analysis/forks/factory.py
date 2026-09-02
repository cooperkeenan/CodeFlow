from tracer.models.index_records import ProjectIndex
from tracer.services.analysis.forks.branch_detector import BranchDetector
from tracer.services.analysis.forks.dispatch_extractor import DispatchExtractor
from tracer.services.analysis.forks.dynamic_detector import DynamicDetector
from tracer.services.analysis.forks.except_detector import ExceptDetector
from tracer.services.analysis.forks.match_detector import MatchDetector
from tracer.services.analysis.forks.polymorphic_detector import PolymorphicDetector
from tracer.services.analysis.forks.route_detector import RouteDetector
from tracer.services.analysis.forks.table_detector import TableDetector
from tracer.services.analysis.routes.django_route_scanner import DjangoRouteScanner
from tracer.services.analysis.routes.fastapi_route_scanner import FastApiRouteScanner


def build_dispatch_extractor(index: ProjectIndex) -> DispatchExtractor:
    detectors = (
        BranchDetector(),
        MatchDetector(),
        ExceptDetector(),
        TableDetector(),
        RouteDetector((FastApiRouteScanner(), DjangoRouteScanner())),
        PolymorphicDetector(),
        DynamicDetector(),
    )
    return DispatchExtractor(index, detectors)
