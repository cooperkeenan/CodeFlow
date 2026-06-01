import logging

from clients.profiler_client import ProfilerClient
from clients.render_client import RenderClient
from clients.tracer_client import TracerClient
from models.analysis_model import AnalyseRequest, AnalyseResponse

from shared.models.profiler_response import ProfileResponse
from shared.models.tracer_request import TracerRequest

logger = logging.getLogger(__name__)


class AnalysisService:
    def __init__(
        self,
        profiler_client: ProfilerClient,
        tracer_client: TracerClient,
        render_client: RenderClient,
    ):
        self._profiler = profiler_client
        self._tracer = tracer_client
        self._render = render_client

    async def analyse(self, request: AnalyseRequest) -> AnalyseResponse:
        logger.info("Starting analysis for: %s", request.repo_name)
        profile = await self._profiler.profile(request)
        return await self._run_from_profile(request.repo_name, request.local_path, profile, request.access_token)

    async def analyse_from_profile(
        self,
        repo_name: str,
        local_path: str | None,
        profile: ProfileResponse,
        access_token: str | None = None,
    ) -> AnalyseResponse:
        logger.info("Resuming from stored profile for: %s", repo_name)
        return await self._run_from_profile(repo_name, local_path, profile, access_token)

    async def analyse_from_trace(self, stored: AnalyseResponse) -> AnalyseResponse:
        logger.info("Re-rendering from stored trace for: %s", stored.repo)
        mermaid = await self._render.render(stored.trace["architecture_type"], stored.trace["diagram_spec"])
        return AnalyseResponse(repo=stored.repo, profile=stored.profile, trace=stored.trace, mermaid=mermaid)

    async def _run_from_profile(
        self,
        repo_name: str,
        local_path: str | None,
        profile: ProfileResponse,
        access_token: str | None = None,
    ) -> AnalyseResponse:
        tracer_request = TracerRequest(
            repo_name=repo_name,
            local_path=local_path,
            access_token=access_token,
            architecture_type=profile.architecture_type,
            language=profile.language,
            blueprint=profile,
        )
        trace = await self._tracer.trace(tracer_request)
        mermaid = await self._render.render(trace["architecture_type"], trace["diagram_spec"])
        logger.info("Render complete for: %s", repo_name)
        return AnalyseResponse(repo=repo_name, profile=profile, trace=trace, mermaid=mermaid)