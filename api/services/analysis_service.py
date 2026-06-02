import logging

from clients.layout_client import LayoutClient
from clients.profiler_client import ProfilerClient
from clients.render_client import RenderClient
from clients.tracer_client import TracerClient
from models.analysis_model import AnalyseRequest, AnalyseResponse
from services.output_persister import OutputPersister

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
    ):
        self._profiler = profiler_client
        self._tracer = tracer_client
        self._render = render_client
        self._layout = layout_client
        self._persister = output_persister

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
        logger.info(
            "[profiler] arch=%s lang=%s modules=%d",
            profile.architecture_type,
            profile.language,
            len(profile.modules),
        )
        self._persister.write_json("profiler.json", profile)
        tracer_request = TracerRequest(
            repo_name=repo_name,
            local_path=local_path,
            access_token=access_token,
            architecture_type=profile.architecture_type,
            language=profile.language,
            blueprint=profile,
        )
        trace = await self._tracer.trace(tracer_request)
        self._persister.write_json("tracer.json", trace)
        spec = trace["diagram_spec"]
        component_count = sum(len(comps) for m in spec.get("modules", []) for comps in m.get("zones", {}).values())
        edge_count = len(spec.get("edges", []))
        edge_types = list({e.get("edge_type") for e in spec.get("edges", [])})
        logger.info(
            "[tracer] modules=%d components=%d edges=%d types=%s",
            len(spec.get("modules", [])),
            component_count,
            edge_count,
            edge_types,
        )
        layout_result = await self._layout.layout(spec)
        self._persister.write_json("layout.json", layout_result)
        layout_hint = layout_result["layout_hint"]
        enriched_spec = layout_result["diagram_spec"]
        primary_components = sum(
            1
            for m in enriched_spec.get("modules", [])
            for comps in m.get("zones", {}).values()
            for c in comps
            if c.get("tier") == "primary"
        )
        logger.info(
            "[layout] archetype=%s order=%s primary_components=%d",
            layout_hint.get("archetype"),
            layout_hint.get("module_order"),
            primary_components,
        )
        trace["diagram_spec"] = enriched_spec
        mermaid = await self._render.render(trace["architecture_type"], trace["diagram_spec"])
        self._persister.write_text("render.mmd", mermaid)
        logger.info("[render] mermaid lines=%d", mermaid.count("\n") + 1)
        return AnalyseResponse(repo=repo_name, profile=profile, trace=trace, mermaid=mermaid)