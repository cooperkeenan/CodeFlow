import logging

from clients.profiler_client import ProfilerClient
from models.analysis_model import AnalyseRequest, AnalyseResponse

logger = logging.getLogger(__name__)


class AnalysisService:
    def __init__(self, profiler_client: ProfilerClient):
        self._profiler = profiler_client

    async def analyse(self, request: AnalyseRequest) -> AnalyseResponse:
        logger.info("Starting analysis for repo: %s", request.repo_name)
        profile = await self._profiler.profile(request)
        logger.info("Profiler complete for repo: %s", request.repo_name)
        return AnalyseResponse(repo=request.repo_name, profile=profile)