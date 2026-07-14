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
        layout_result = await self._layout.layout(stored.trace["diagram_spec"])
        self._persister.write_json("layout.json", layout_result)
        diagram_templates = layout_result["diagram_templates"]
        stored.trace["diagram_templates"] = diagram_templates
        diagram = await self._render.render(diagram_templates)
        self._persister.write_json("render.json", diagram)
        return AnalyseResponse(repo=stored.repo, profile=stored.profile, trace=stored.trace, diagram=diagram)

    async def analyse_from_layout(self, stored: AnalyseResponse, diagram_templates: dict) -> AnalyseResponse:
        logger.info("Re-rendering from stored layout for: %s", stored.repo)
        diagram = await self._render.render(diagram_templates)
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

        spec = trace["diagram_spec"]
        component_count = sum(len(cs) for m in spec.get("modules", []) for cs in m.get("zones", {}).values())
        logger.info("[tracer] modules=%d components=%d edges=%d",
                    len(spec.get("modules", [])), component_count, len(spec.get("edges", [])))
        
        layout_result = await self._layout.layout(spec)
        self._progress.complete("layout")
        self._persister.write_json("layout.json", layout_result)
        
        layout_hint = layout_result["layout_hint"]
        enriched_spec = layout_result["diagram_spec"]
        diagram_templates = layout_result["diagram_templates"]
        system_tmpl = diagram_templates.get("system", {})
        logger.info("[layout] archetype=%s order=%s", layout_hint.get("archetype"), layout_hint.get("module_order"))
        logger.info("[template] system_type=%s views=%d", system_tmpl.get("type"), len(diagram_templates))
        trace["diagram_spec"] = enriched_spec
        trace["diagram_templates"] = diagram_templates
        self._persister.write_json("layout_reasoning.json", self._build_reasoning(diagram_templates))
        diagram = await self._render.render(diagram_templates)
        self._progress.complete("render")
        self._persister.write_json("render.json", diagram)
        logger.info("[render] views=%d", len(diagram.get("views", {})))
        return AnalyseResponse(repo=repo_name, profile=profile, trace=trace, diagram=diagram)

    def _build_reasoning(self, diagram_templates: dict) -> dict:
        return {
            view_id: {
                "type": tmpl.get("type"),
                "rationale": tmpl.get("meta", {}).get("rationale", ""),
                "node_count": len(tmpl.get("nodes", [])),
                "edge_count": len(tmpl.get("edges", [])),
            }
            for view_id, tmpl in diagram_templates.items()
            if isinstance(tmpl, dict)
        }
