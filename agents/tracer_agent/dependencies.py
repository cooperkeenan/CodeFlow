import anthropic
import httpx
from core.config import Settings, get_settings
from fastapi import Depends, Request
from services.ast_service import AstService
from services.call_graph_service import CallGraphService
from services.chunk_context_builder import ChunkContextBuilder
from services.chunk_tracer import ChunkTracer
from services.breadcrumb_builder import BreadcrumbBuilder
from services.component_placer import ComponentPlacer
from services.correction_prompt_builder import CorrectionPromptBuilder
from services.edge_recovery import EdgeRecovery
from services.evidence_service import EvidenceService
from services.file_fetch_service import FileFetchService
from services.graph_validator import GraphValidator
from services.line_range_enricher import LineRangeEnricher
from services.raw_merger import RawMerger
from services.source_persist_service import SourcePersistService
from services.spec_assembler import SpecAssembler
from services.tracer_service import TracerService
from services.tree_traversal_partitioner import TreeTraversalPartitioner
from tools.build_call_graph_tool import BuildCallGraphTool
from tools.build_evidence_tool import BuildEvidenceTool
from tools.fetch_layer_files_tool import FetchLayerFilesTool

from shared.code_store.code_store import CodeStore
from shared.code_store.neon_code_store import NeonCodeStore


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


def get_spec_assembler() -> SpecAssembler:
    return SpecAssembler(ComponentPlacer())


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


def get_tree_traversal_partitioner(
    settings: Settings = Depends(get_settings),
) -> TreeTraversalPartitioner:
    return TreeTraversalPartitioner(
        settings.TRACER_CHUNK_TOKEN_BUDGET, settings.TRACER_CHUNK_MAX_COMPONENTS
    )


def get_breadcrumb_builder() -> BreadcrumbBuilder:
    return BreadcrumbBuilder()


def get_chunk_context_builder() -> ChunkContextBuilder:
    return ChunkContextBuilder()


def get_raw_merger() -> RawMerger:
    return RawMerger()


def get_edge_recovery() -> EdgeRecovery:
    return EdgeRecovery()


def get_graph_validator() -> GraphValidator:
    return GraphValidator()


def get_line_range_enricher() -> LineRangeEnricher:
    return LineRangeEnricher()


def get_code_store(
    settings: Settings = Depends(get_settings),
) -> CodeStore:
    return NeonCodeStore(settings.DATABASE_URL)


def get_source_persist_service(
    code_store: CodeStore = Depends(get_code_store),
) -> SourcePersistService:
    return SourcePersistService(code_store)


def get_correction_prompt_builder() -> CorrectionPromptBuilder:
    return CorrectionPromptBuilder()


def get_chunk_tracer(
    anthropic_client: anthropic.AsyncAnthropic = Depends(get_anthropic_client),
    spec_assembler: SpecAssembler = Depends(get_spec_assembler),
    graph_validator: GraphValidator = Depends(get_graph_validator),
    correction_builder: CorrectionPromptBuilder = Depends(get_correction_prompt_builder),
) -> ChunkTracer:
    return ChunkTracer(anthropic_client, spec_assembler, graph_validator, correction_builder)


def get_tracer_service(
    fetch_layer_files_tool: FetchLayerFilesTool = Depends(get_fetch_layer_files_tool),
    build_call_graph_tool: BuildCallGraphTool = Depends(get_build_call_graph_tool),
    build_evidence_tool: BuildEvidenceTool = Depends(get_build_evidence_tool),
    spec_assembler: SpecAssembler = Depends(get_spec_assembler),
    partitioner: TreeTraversalPartitioner = Depends(get_tree_traversal_partitioner),
    context_builder: ChunkContextBuilder = Depends(get_chunk_context_builder),
    chunk_tracer: ChunkTracer = Depends(get_chunk_tracer),
    raw_merger: RawMerger = Depends(get_raw_merger),
    edge_recovery: EdgeRecovery = Depends(get_edge_recovery),
    graph_validator: GraphValidator = Depends(get_graph_validator),
    breadcrumb_builder: BreadcrumbBuilder = Depends(get_breadcrumb_builder),
    line_range_enricher: LineRangeEnricher = Depends(get_line_range_enricher),
    source_persist: SourcePersistService = Depends(get_source_persist_service),
) -> TracerService:
    return TracerService(
        fetch_layer_files_tool,
        build_call_graph_tool,
        build_evidence_tool,
        spec_assembler,
        partitioner,
        context_builder,
        chunk_tracer,
        raw_merger,
        edge_recovery,
        graph_validator,
        breadcrumb_builder,
        line_range_enricher,
        source_persist,
    )
