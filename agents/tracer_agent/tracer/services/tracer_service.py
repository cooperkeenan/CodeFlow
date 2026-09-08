import logging
from pathlib import Path

from tracer.models.tracer_model import TracerResponse
from tracer.services.analysis.flow_pipeline import FlowPipeline
from tracer.services.analysis.stage_reporter import StageReporter
from tracer.services.evidence.file_fetch_service import FileFetchService
from tracer.services.source_persist_service import SourcePersistService

from shared.models.repo_blueprint import RepoBlueprint
from shared.models.tracer_request import TracerRequest

logger = logging.getLogger(__name__)


class TracerService:
    def __init__(
        self,
        file_fetch_service: FileFetchService,
        source_persist: SourcePersistService,
        flow_pipeline: FlowPipeline,
        stages: StageReporter,
    ) -> None:
        self._files = file_fetch_service
        self._source_persist = source_persist
        self._pipeline = flow_pipeline
        self._stages = stages

    async def trace(self, request: TracerRequest) -> TracerResponse:
        self._stages.start(request.repo_name)
        try:
            return await self._trace(request)
        except Exception as exc:
            self._stages.fail(f"{type(exc).__name__}: {exc}" if str(exc) else type(exc).__name__)
            raise

    async def _trace(self, request: TracerRequest) -> TracerResponse:
        directories = self._minimal_dirs(request.blueprint)
        self._stages.begin("fetch", f"{len(directories)} source directories")
        temp_dir, file_paths = await self._files.fetch_files(
            directories=directories,
            access_token=request.access_token,
            repo_name=request.repo_name,
            local_path=request.local_path,
            archive_gz=request.archive_gz,
        )
        if not file_paths:
            raise ValueError("No source files fetched for tracing")
        self._stages.begin("read", f"{len(file_paths)} files")
        await self._source_persist.persist(request.repo_name, temp_dir, file_paths)
        files = self._read_files(file_paths, Path(temp_dir))
        graph = self._pipeline.run(request.repo_name, files)
        self._stages.note(
            f"flow: {len(graph.lanes)} lane(s), {len(graph.nodes)} node(s), "
            f"{len(graph.edges)} edge(s)"
        )
        return TracerResponse(flow_graph=graph)

    def _read_files(self, file_paths: list[str], base: Path) -> dict[str, str]:
        files: dict[str, str] = {}
        for fp in file_paths:
            try:
                content = Path(fp).read_text(encoding="utf-8")
                try:
                    rel = Path(fp).relative_to(base).as_posix()
                except ValueError:
                    rel = Path(fp).name
                files[rel] = content
            except OSError:
                logger.warning("Could not read %s", fp)
        return files

    def _minimal_dirs(self, blueprint: RepoBlueprint) -> list[str]:
        dirs = sorted({d for m in blueprint.modules for z in m.zones for d in z.directories})
        return [d for d in dirs if not any(o != d and d.startswith(o) for o in dirs)]
