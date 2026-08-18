from pathlib import Path

import httpx
from core.config import Settings, get_settings
from fastapi import Depends, Request
from services.analysis.decision_judge_factory import build_decision_judge
from services.analysis.effect_detector_factory import build_effect_detector
from services.analysis.flow_namer_factory import build_flow_namer
from services.analysis.flow_pipeline import FlowPipeline
from services.analysis.flow_reviewer_factory import build_flow_reviewer
from services.analysis.flow_stitcher_factory import build_flow_stitcher
from services.analysis.visibility_budgeter_factory import build_visibility_budgeter
from services.analysis.project_indexer_factory import build_project_indexer
from services.evidence.file_fetch_service import FileFetchService
from services.evidence.github_file_fetcher import GitHubFileFetcher
from services.source_persist_service import SourcePersistService
from services.tracer_service import TracerService

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


def get_flow_pipeline(
    settings: Settings = Depends(get_settings),
) -> FlowPipeline:
    return FlowPipeline(
        build_project_indexer(),
        build_effect_detector(),
        build_flow_stitcher(settings.ANTHROPIC_API_KEY),
        build_visibility_budgeter(),
        judge=build_decision_judge(settings.ANTHROPIC_API_KEY, _CACHE_ROOT / "decision_verdicts.json"),
        namer=build_flow_namer(settings.ANTHROPIC_API_KEY, _CACHE_ROOT / "node_names.json"),
        reviewer=build_flow_reviewer(settings.ANTHROPIC_API_KEY, _CACHE_ROOT / "review_findings.json"),
    )


def get_tracer_service(
    file_fetch_service: FileFetchService = Depends(get_file_fetch_service),
    source_persist: SourcePersistService = Depends(get_source_persist_service),
    flow_pipeline: FlowPipeline = Depends(get_flow_pipeline),
) -> TracerService:
    return TracerService(file_fetch_service, source_persist, flow_pipeline)
