import logging

from models.evidence_chunk import EvidenceChunk
from models.tracer_model import TracerResponse
from services.tracing.breadcrumb_builder import BreadcrumbBuilder
from services.evidence.call_graph_service import CallGraphService
from services.tracing.chunk_context_builder import ChunkContextBuilder
from services.tracing.chunk_tracer import ChunkTracer
from services.assembly.edge_recovery import EdgeRecovery
from services.evidence.evidence_service import EvidenceService
from services.evidence.file_fetch_service import FileFetchService
from services.assembly.graph_validator import GraphValidator
from services.line_range_enricher import LineRangeEnricher
from services.assembly.raw_merger import RawMerger
from services.source_persist_service import SourcePersistService
from services.assembly.spec_assembler import SpecAssembler
from services.tracing.tree_traversal_partitioner import TreeTraversalPartitioner

from shared.models.repo_blueprint import RepoBlueprint
from shared.models.tracer_request import TracerRequest

logger = logging.getLogger(__name__)


class TracerService:
    def __init__(
        self,
        file_fetch_service: FileFetchService,
        call_graph_service: CallGraphService,
        evidence_service: EvidenceService,
        spec_assembler: SpecAssembler,
        partitioner: TreeTraversalPartitioner,
        context_builder: ChunkContextBuilder,
        chunk_tracer: ChunkTracer,
        raw_merger: RawMerger,
        edge_recovery: EdgeRecovery,
        graph_validator: GraphValidator,
        breadcrumb_builder: BreadcrumbBuilder,
        line_range_enricher: LineRangeEnricher,
        source_persist: SourcePersistService,
    ) -> None:
        self._files = file_fetch_service
        self._call_graph = call_graph_service
        self._evidence = evidence_service
        self._assembler = spec_assembler
        self._partitioner = partitioner
        self._context_builder = context_builder
        self._chunk_tracer = chunk_tracer
        self._raw_merger = raw_merger
        self._edge_recovery = edge_recovery
        self._graph_validator = graph_validator
        self._breadcrumb_builder = breadcrumb_builder
        self._line_range_enricher = line_range_enricher
        self._source_persist = source_persist

    async def trace(self, request: TracerRequest) -> TracerResponse:
        logger.info("Tracing repo: %s", request.repo_name)
        evidence = await self._gather_evidence(request)
        chunks = self._partitioner.partition(evidence, request.blueprint)
        logger.info("Tracing %s in %d chunks", request.repo_name, len(chunks))
        context = self._context_builder.build(request.blueprint, evidence)
        raws = await self._trace_sequential(chunks, context, request.blueprint, request.architecture_type)
        merged = self._raw_merger.merge(raws)
        spec = self._assembler.assemble(request.blueprint, merged, request.architecture_type)
        spec = self._line_range_enricher.enrich(spec, evidence.get("signatures", {}))
        spec = self._edge_recovery.recover(spec, evidence)
        spec = self._graph_validator.validate(spec, evidence).fixed_spec
        component_count = sum(len(comps) for m in spec.modules for comps in m.zones.values())
        edge_types: dict[str, int] = {}
        for e in spec.edges:
            edge_types[e.edge_type] = edge_types.get(e.edge_type, 0) + 1
        logger.info(
            "Trace: modules=%d components=%d edges=%d %s",
            len(spec.modules),
            component_count,
            len(spec.edges),
            " ".join(f"{k}={v}" for k, v in sorted(edge_types.items())),
        )
        return TracerResponse(architecture_type=request.architecture_type, diagram_spec=spec)

    async def _trace_sequential(
        self,
        chunks: list[EvidenceChunk],
        context: str,
        blueprint: RepoBlueprint,
        architecture_type: str,
    ) -> list[dict]:
        raws: list[dict] = []
        for i, chunk in enumerate(chunks):
            if i > 0:
                crumb = self._breadcrumb_builder.build(raws, chunk.label)
                chunk = EvidenceChunk(chunk.label, chunk.evidence, breadcrumb=crumb)
            raws.append(await self._chunk_tracer.trace_chunk(chunk, context, blueprint, architecture_type))
        return raws

    async def _gather_evidence(self, request: TracerRequest) -> dict:
        directories = self._minimal_dirs(request.blueprint)
        temp_dir, file_paths = await self._files.fetch_files(
            directories=directories,
            access_token=request.access_token,
            repo_name=request.repo_name,
            local_path=request.local_path,
            archive_gz=request.archive_gz,
        )
        if not file_paths:
            raise ValueError("No source files fetched for tracing")
        await self._source_persist.persist(request.repo_name, temp_dir, file_paths)
        call_graph = self._call_graph.build(temp_dir, file_paths, request.entry_point_hint)
        return self._evidence.build(file_paths, call_graph, temp_dir)

    def _minimal_dirs(self, blueprint: RepoBlueprint) -> list[str]:
        dirs = sorted({d for m in blueprint.modules for z in m.zones for d in z.directories})
        return [d for d in dirs if not any(o != d and d.startswith(o) for o in dirs)]
