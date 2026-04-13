import logging

from clients.profiler_client import ProfilerClient
from clients.tracer_client import TracerClient
from models.analysis_model import AnalyseRequest, AnalyseResponse

logger = logging.getLogger(__name__)


class AnalysisService:
    def __init__(self, profiler_client: ProfilerClient, tracer_client: TracerClient):
        self._profiler = profiler_client
        self._tracer = tracer_client

    async def analyse(self, request: AnalyseRequest) -> AnalyseResponse:
        logger.info("Starting analysis for: %s", request.repo_name)

        profile = await self._profiler.profile(request)
        logger.info("Profiler complete, starting tracer")

        trace = await self._tracer.trace(request, profile)
        logger.info("Tracer complete for: %s", request.repo_name)

        return AnalyseResponse(
            repo=request.repo_name,
            profile=profile,
            trace=trace,
        )