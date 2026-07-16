from models.call_site import CallSite
from models.dispatch_site import DispatchSite
from models.project_index import ProjectIndex
from services.analysis.dispatch_detector import DispatchDetectionContext, DispatchDetector


class DispatchExtractor:
    def __init__(self, index: ProjectIndex, detectors: tuple[DispatchDetector, ...]) -> None:
        self._index = index
        self._detectors = detectors

    def extract(self, callsites: tuple[CallSite, ...]) -> tuple[DispatchSite, ...]:
        context = DispatchDetectionContext(index=self._index, callsites=callsites)
        sites: list[DispatchSite] = []
        for detector in self._detectors:
            sites.extend(detector.detect(context))
        return tuple(sites)
