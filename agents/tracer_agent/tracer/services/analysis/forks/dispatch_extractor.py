from tracer.models.call_records import CallSite
from tracer.models.index_records import ProjectIndex
from tracer.models.sites import DispatchSite
from tracer.services.analysis.contracts import DispatchDetectionContext
from tracer.services.analysis.forks.dispatch_detector import DispatchDetector


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
