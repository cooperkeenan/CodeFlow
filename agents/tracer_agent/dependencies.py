import httpx
from core.config import Settings, get_settings
from fastapi import Depends, Request
from services.analysis.effect_detector_factory import build_effect_detector
from services.analysis.flow_pipeline import FlowPipeline
from services.analysis.flow_stitcher_factory import build_flow_stitcher
from services.analysis.page_budgeter_factory import build_page_budgeter
from services.analysis.project_indexer_factory import build_project_indexer
from services.evidence.file_fetch_service import FileFetchService
from services.source_persist_service import SourcePersistService
from services.tracer_service import TracerService

from shared.code_store.code_store import CodeStore
from shared.code_store.neon_code_store import NeonCodeStore


def get_http_client(request: Request) -> httpx.AsyncClient:
    return request.app.state.http_client


def get_file_fetch_service(
    http_client: httpx.AsyncClient = Depends(get_http_client),
) -> FileFetchService:
    return FileFetchService(http_client)


def get_code_store(
    settings: Settings = Depends(get_settings),
) -> CodeStore:
    return NeonCodeStore(settings.DATABASE_URL)


def get_source_persist_service(
    code_store: CodeStore = Depends(get_code_store),
) -> SourcePersistService:
    return SourcePersistService(code_store)


def get_flow_pipeline() -> FlowPipeline:
    return FlowPipeline(
        build_project_indexer(),
        build_effect_detector(),
        build_flow_stitcher(),
        build_page_budgeter(),
    )


def get_tracer_service(
    file_fetch_service: FileFetchService = Depends(get_file_fetch_service),
    source_persist: SourcePersistService = Depends(get_source_persist_service),
    flow_pipeline: FlowPipeline = Depends(get_flow_pipeline),
) -> TracerService:
    return TracerService(file_fetch_service, source_persist, flow_pipeline)
