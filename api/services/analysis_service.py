import logging

from clients.layout_client import LayoutClient
from clients.profiler_client import ProfilerClient
from clients.render_client import RenderClient
from clients.tracer_client import TracerClient
from models.analysis_model import AnalyseRequest, AnalyseResponse
from services.output_persister import OutputPersister
from services.progress_tracker import ProgressTracker

from shared.models.profiler_response import ProfileResponse
from shared.models.tracer_request import TracerRequest

logger = logging.getLogger(__name__)


class AnalysisService:
    def __init__(
        self,
        profiler_client: ProfilerClient,
        tracer_client: TracerClient,
        render_client: RenderClient,
        layout_client: LayoutClient,
        output_persister: OutputPersister,
        progress: ProgressTracker,
    ):
        self._profiler = profiler_client
        self._tracer = tracer_client
        self._render = render_client
        self._layout = layout_client
        self._persister = output_persister
        self._progress = progress

    async def analyse(self, request: AnalyseRequest) -> AnalyseResponse:
        self._progress.start()
        logger.info("Starting analysis for: %s", request.repo_name)
        profile = await self._profiler.profile(request)
        self._progress.complete("profiler")
        return await self._run_from_profile(request.repo_name, request.local_path, profile, request.access_token, request.archive_gz)

    async def analyse_from_profile(
        self, repo_name: str, local_path: str | None,
        profile: ProfileResponse, access_token: str | None = None,
    ) -> AnalyseResponse:
        self._progress.start()
        self._progress.complete("profiler")
        logger.info("Resuming from stored profile for: %s", repo_name)
        return await self._run_from_profile(repo_name, local_path, profile, access_token)

    async def analyse_from_trace(self, stored: AnalyseResponse) -> AnalyseResponse:
        logger.info("Re-running layout+render from stored trace for: %s", stored.repo)
        labeled = await self._layout.layout(stored.trace["flow_graph"])
        self._persister.write_json("layout.json", labeled)
        flow_graph = labeled["flow_graph"]
        stored.trace["flow_graph"] = flow_graph
        diagram = await self._render.render(flow_graph)
        self._persister.write_json("render.json", diagram)
        return AnalyseResponse(repo=stored.repo, profile=stored.profile, trace=stored.trace, diagram=diagram)

    async def analyse_from_layout(self, stored: AnalyseResponse, flow_graph: dict) -> AnalyseResponse:
        logger.info("Re-rendering from stored layout for: %s", stored.repo)
        diagram = await self._render.render(flow_graph)
        self._persister.write_json("render.json", diagram)
        return AnalyseResponse(repo=stored.repo, profile=stored.profile, trace=stored.trace, diagram=diagram)

    async def _run_from_profile(
        self, repo_name: str, local_path: str | None,
        profile: ProfileResponse, access_token: str | None = None,
        archive_gz: str | None = None,
    ) -> AnalyseResponse:
        logger.info("[profiler] arch=%s lang=%s modules=%d", profile.architecture_type, profile.language, len(profile.modules))
        self._persister.write_json("profiler.json", profile)
        
        trace = await self._tracer.trace(TracerRequest(
            repo_name=repo_name, local_path=local_path, access_token=access_token,
            archive_gz=archive_gz,
            architecture_type=profile.architecture_type, language=profile.language, blueprint=profile,
        ))
        self._progress.complete("tracer")
        self._persister.write_json("tracer.json", trace)

        flow_graph = trace["flow_graph"]
        logger.info("[tracer] lanes=%d nodes=%d edges=%d",
                    len(flow_graph.get("lanes", [])), len(flow_graph.get("nodes", [])),
                    len(flow_graph.get("edges", [])))

        labeled = await self._layout.layout(flow_graph)
        self._progress.complete("layout")
        self._persister.write_json("layout.json", labeled)
        flow_graph = labeled["flow_graph"]
        trace["flow_graph"] = flow_graph

        diagram = await self._render.render(flow_graph)
        self._progress.complete("render")
        self._persister.write_json("render.json", diagram)
        logger.info("[render] nodes=%d", len(diagram.get("view", {}).get("nodes", [])))
        return AnalyseResponse(repo=repo_name, profile=profile, trace=trace, diagram=diagram)
