from models.project_index import ProjectIndex
from services.analysis.branch_detector import BranchDetector
from services.analysis.dispatch_extractor import DispatchExtractor
from services.analysis.django_route_scanner import DjangoRouteScanner
from services.analysis.dynamic_detector import DynamicDetector
from services.analysis.except_detector import ExceptDetector
from services.analysis.fastapi_route_scanner import FastApiRouteScanner
from services.analysis.match_detector import MatchDetector
from services.analysis.polymorphic_detector import PolymorphicDetector
from services.analysis.route_detector import RouteDetector
from services.analysis.table_detector import TableDetector


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
