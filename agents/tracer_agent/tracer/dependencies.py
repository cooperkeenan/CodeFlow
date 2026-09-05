from pathlib import Path

import httpx
from fastapi import Depends, Request
from tracer.core.config import Settings, get_settings
from tracer.services.analysis.budget.factory import (
    build_visibility_budgeter,
)
from tracer.services.analysis.effects.factory import (
    build_effect_detector,
)
from tracer.services.analysis.flow_pipeline import FlowPipeline
from tracer.services.analysis.indexing.factory import (
    build_project_indexer,
)
from tracer.services.analysis.labelling.factory import (
    build_flow_namer,
    build_flow_reviewer,
)
from tracer.services.analysis.significance.factory import (
    build_decision_judge,
)
from tracer.services.analysis.stage_reporter import StageReporter
from tracer.services.analysis.stitch.factory import build_flow_stitcher
from tracer.services.evidence.file_fetch_service import FileFetchService
from tracer.services.evidence.github_file_fetcher import GitHubFileFetcher
from tracer.services.source_persist_service import SourcePersistService
from tracer.services.tracer_service import TracerService

from shared.code_store.code_store import CodeStore
from shared.code_store.neon_code_store import NeonCodeStore

_PARENTS = Path(__file__).resolve().parents
_CACHE_ROOT = (_PARENTS[2] if len(_PARENTS) > 2 else _PARENTS[0]) / ".cache"


def get_http_client(request: Request) -> httpx.AsyncClient:
    return request.app.state.http_client


def get_file_fetch_service(
    http_client: httpx.AsyncClient = Depends(get_http_client),
) -> FileFetchService:
    return FileFetchService(GitHubFileFetcher(http_client))


def get_code_store(
    settings: Settings = Depends(get_settings),
) -> CodeStore:
    return NeonCodeStore(settings.DATABASE_URL)


def get_source_persist_service(
    code_store: CodeStore = Depends(get_code_store),
) -> SourcePersistService:
    return SourcePersistService(code_store)


def get_stage_reporter(request: Request) -> StageReporter:
    return request.app.state.stage_reporter


def get_flow_pipeline(
    settings: Settings = Depends(get_settings),
    stages: StageReporter = Depends(get_stage_reporter),
) -> FlowPipeline:
    return FlowPipeline(
        build_project_indexer(),
        build_effect_detector(),
        build_flow_stitcher(settings.ANTHROPIC_API_KEY),
        build_visibility_budgeter(),
        judge=build_decision_judge(settings.ANTHROPIC_API_KEY, _CACHE_ROOT / "decision_verdicts.json"),
        namer=build_flow_namer(settings.ANTHROPIC_API_KEY, _CACHE_ROOT / "node_names.json"),
        reviewer=build_flow_reviewer(settings.ANTHROPIC_API_KEY, _CACHE_ROOT / "review_findings.json"),
        stages=stages,
    )


def get_tracer_service(
    file_fetch_service: FileFetchService = Depends(get_file_fetch_service),
    source_persist: SourcePersistService = Depends(get_source_persist_service),
    flow_pipeline: FlowPipeline = Depends(get_flow_pipeline),
) -> TracerService:
    return TracerService(file_fetch_service, source_persist, flow_pipeline)
