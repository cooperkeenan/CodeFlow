import logging
from clients.profiler_client import ProfilerClient
from clients.tracer_client import TracerClient
from models.analysis_model import AnalyseRequest, AnalyseResponse

from shared.models.profiler_response import ProfileResponse
from shared.models.tracer_request import TracerRequest

logger = logging.getLogger(__name__)


class AnalysisService:
    def __init__(self, profiler_client: ProfilerClient, tracer_client: TracerClient):
        self._profiler = profiler_client
        self._tracer = tracer_client

    async def analyse(self, request: AnalyseRequest) -> AnalyseResponse:
        logger.info("Starting analysis for: %s", request.repo_name)
        profile = await self._profiler.profile(request)
        return await self._run_from_profile(request.repo_name, request.local_path, profile)

    async def analyse_from_profile(
        self,
        repo_name: str,
        local_path: str | None,
        profile: ProfileResponse,
    ) -> AnalyseResponse:
        logger.info("Resuming from stored profile for: %s", repo_name)
        return await self._run_from_profile(repo_name, local_path, profile)

    async def analyse_from_trace(self, stored: AnalyseResponse) -> AnalyseResponse:
        logger.info("Resuming from stored trace for: %s", stored.repo)
        return stored

    async def _run_from_profile(
        self,
        repo_name: str,
        local_path: str | None,
        profile: ProfileResponse,
    ) -> AnalyseResponse:
        tracer_request = TracerRequest(
            repo_name=repo_name,
            local_path=local_path,
            architecture_type=profile.architecture_type,
            language=profile.language,
            entry_point_hint=profile.entry_point_hint,
            layer_hints=profile.layer_hints,
        )
        trace = await self._tracer.trace(tracer_request)
        logger.info("Tracer complete for: %s", repo_name)
        return AnalyseResponse(repo=repo_name, profile=profile, trace=trace)