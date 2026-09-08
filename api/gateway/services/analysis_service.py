from gateway.clients.profiler_client import ProfilerClient
from gateway.clients.render_client import RenderClient
from gateway.clients.tracer_client import TracerClient
from gateway.models.repo_map_model import AnalyseRequest, AnalyseResponse
from gateway.services.output_persister import OutputPersister
from gateway.services.progress_tracker import ProgressTracker

from shared.models.profiler_response import ProfileResponse
from shared.models.tracer_request import TracerRequest


class AnalysisService:
    def __init__(
        self,
        profiler_client: ProfilerClient,
        tracer_client: TracerClient,
        render_client: RenderClient,
        output_persister: OutputPersister,
        progress: ProgressTracker,
    ):
        self._profiler = profiler_client
        self._tracer = tracer_client
        self._render = render_client
        self._persister = output_persister
        self._progress = progress

    async def analyse(self, request: AnalyseRequest) -> AnalyseResponse:
        self._progress.begin("profiler", f"Reading the layout of {request.repo_name}")
        self._progress.step("calling the profiler agent — this can take minutes on a large repo")
        profile = await self._profiler.profile(request)
        self._progress.complete(
            "profiler",
            f"profiler: {len(profile.modules)} module(s), "
            f"arch={profile.architecture_type}, lang={profile.language}",
        )
        return await self._run_from_profile(
            request.repo_name, request.local_path, profile,
            request.access_token, request.archive_gz,
        )

    async def _run_from_profile(
        self, repo_name: str, local_path: str | None,
        profile: ProfileResponse, access_token: str | None = None,
        archive_gz: str | None = None,
    ) -> AnalyseResponse:
        self._persister.write_json("profiler.json", profile)
        self._progress.begin("tracer", f"Indexing {repo_name} and judging its decisions")
        for module in profile.modules:
            self._progress.step(f"module {module.name} zones={[z.name for z in module.zones]}")
        trace = await self._tracer.trace(TracerRequest(
            repo_name=repo_name, local_path=local_path, access_token=access_token,
            archive_gz=archive_gz,
            architecture_type=profile.architecture_type, language=profile.language, blueprint=profile,
        ))
        self._persister.write_json("tracer.json", trace)
        flow_graph = trace["flow_graph"]
        self._progress.complete(
            "tracer",
            f"tracer: {len(flow_graph.get('lanes', []))} lane(s), "
            f"{len(flow_graph.get('nodes', []))} node(s), "
            f"{len(flow_graph.get('edges', []))} edge(s)",
        )
        self._progress.begin("render", "Placing nodes and routing edges")
        diagram = await self._render.render(flow_graph)
        self._persister.write_json("render.json", diagram)
        positioned = len(diagram.get("view", {}).get("nodes", []))
        self._progress.complete("render", f"render: {positioned} positioned node(s)")
        return AnalyseResponse(repo=repo_name, profile=profile, trace=trace, diagram=diagram)
