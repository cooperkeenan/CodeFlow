import logging
from inspect import signature

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

        profile: ProfileResponse = await self._profiler.profile(request)
        logger.info("Profiler complete, starting tracer")

        tracer_request = TracerRequest(
                access_token=request.access_token,
                repo_name=request.repo_name,
                local_path=request.local_path,
                architecture_type=profile.architecture_type,
                language=profile.language,
                entry_point_hint=profile.entry_point_hint,
                layer_hints=profile.layer_hints,
        )
        logger.info(
            "Invoking tracer client %s.trace with signature %s",
            type(self._tracer).__module__,
            signature(type(self._tracer).trace),
        )
        trace = await self._tracer.trace(tracer_request)
        logger.info("Tracer complete for repo: %s", request.repo_name)

        return AnalyseResponse(repo=request.repo_name, profile=profile, trace=trace)
