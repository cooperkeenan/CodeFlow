import anthropic
import httpx
from core.config import Settings, get_settings
from fastapi import Depends, Request
from services.ast_service import AstService
from services.call_graph_service import CallGraphService
from services.evidence_service import EvidenceService
from services.file_fetch_service import FileFetchService
from services.tracer_service import TracerService
from tools.build_call_graph_tool import BuildCallGraphTool
from tools.build_evidence_tool import BuildEvidenceTool
from tools.fetch_layer_files_tool import FetchLayerFilesTool
from tools.get_diagram_template_tool import GetDiagramTemplateTool


def get_http_client(request: Request) -> httpx.AsyncClient:
    return request.app.state.http_client


def get_file_fetch_service(
    http_client: httpx.AsyncClient = Depends(get_http_client),
) -> FileFetchService:
    return FileFetchService(http_client)


def get_call_graph_service() -> CallGraphService:
    return CallGraphService()


def get_ast_service() -> AstService:
    return AstService()


def get_evidence_service(
    ast_service: AstService = Depends(get_ast_service),
) -> EvidenceService:
    return EvidenceService(ast_service)


def get_fetch_layer_files_tool(
    service: FileFetchService = Depends(get_file_fetch_service),
) -> FetchLayerFilesTool:
    return FetchLayerFilesTool(service)


def get_build_call_graph_tool(
    service: CallGraphService = Depends(get_call_graph_service),
) -> BuildCallGraphTool:
    return BuildCallGraphTool(service)


def get_diagram_template_tool() -> GetDiagramTemplateTool:
    return GetDiagramTemplateTool()


def get_build_evidence_tool(
    service: EvidenceService = Depends(get_evidence_service),
) -> BuildEvidenceTool:
    return BuildEvidenceTool(service)


def get_anthropic_client(
    settings: Settings = Depends(get_settings),
) -> anthropic.AsyncAnthropic:
    http_client = httpx.AsyncClient(verify=False)
    return anthropic.AsyncAnthropic(
        api_key=settings.ANTHROPIC_API_KEY,
        http_client=http_client,
    )


def get_tracer_service(
    fetch_layer_files_tool: FetchLayerFilesTool = Depends(get_fetch_layer_files_tool),
    build_call_graph_tool: BuildCallGraphTool = Depends(get_build_call_graph_tool),
    diagram_template_tool: GetDiagramTemplateTool = Depends(get_diagram_template_tool),
    build_evidence_tool: BuildEvidenceTool = Depends(get_build_evidence_tool),
    anthropic_client: anthropic.AsyncAnthropic = Depends(get_anthropic_client),
) -> TracerService:
    return TracerService(
        fetch_layer_files_tool,
        build_call_graph_tool,
        diagram_template_tool,
        build_evidence_tool,
        anthropic_client,
    )
