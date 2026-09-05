from pathlib import Path

from fastapi import Depends

from gateway.clients.explain_client import ExplainClient
from gateway.clients.profiler_client import ProfilerClient
from gateway.clients.render_client import RenderClient
from gateway.clients.tracer_client import TracerClient
from gateway.core.config import Settings, get_settings
from gateway.deps.auth import get_token_hasher
from gateway.deps.clients import (
    get_explain_client,
    get_github_service,
    get_profiler_client,
    get_render_client,
    get_tracer_client,
)
from gateway.deps.stores import (
    get_code_store,
    get_diagram_edit_store,
    get_explanation_store,
    get_progress_tracker,
    get_repo_map_store,
    get_token_store,
    get_user_store,
)
from gateway.services.analysis_service import AnalysisService
from gateway.services.archive_extractor import ArchiveExtractor
from gateway.services.ci_ingest_service import CiIngestService
from gateway.services.diagram_edit_service import DiagramEditService
from gateway.services.endpoint_view_service import EndpointViewService
from gateway.services.github_ci_service import GitHubCiService
from gateway.services.github_repo_service import GitHubRepoService
from gateway.services.github_service import GitHubService
from gateway.services.local_ci_service import LocalCiService
from gateway.services.node_explain_service import NodeExplainService
from gateway.services.output_persister import OutputPersister
from gateway.services.progress_tracker import ProgressTracker
from gateway.services.repo_map_service import RepoMapService
from gateway.services.source_slicer import SourceSlicer
from gateway.services.step_tree_labeler import StepTreeLabeler
from gateway.services.symbol_context_resolver import SymbolContextResolver
from gateway.services.token_hasher import TokenHasher
from gateway.services.token_service import TokenService
from shared.access_token_store.access_token_store import AccessTokenStore
from shared.code_store.code_store import CodeStore
from shared.diagram_edit_store.diagram_edit_store import DiagramEditStore
from shared.flow_endpoints.endpoint_catalog import EndpointCatalog
from shared.flow_endpoints.endpoint_subgraph import EndpointSubgraph
from shared.explanation_store.explanation_store import ExplanationStore
from shared.repo_map_store.repo_map_store import RepoMapStore
from shared.user_store.user_store import UserStore

_REPO_ROOT = Path(__file__).resolve().parents[2]


def get_analysis_service(
    profiler_client: ProfilerClient = Depends(get_profiler_client),
    tracer_client: TracerClient = Depends(get_tracer_client),
    render_client: RenderClient = Depends(get_render_client),
    progress_tracker: ProgressTracker = Depends(get_progress_tracker),
) -> AnalysisService:
    persister = OutputPersister(_REPO_ROOT / "outputs")
    return AnalysisService(profiler_client, tracer_client, render_client, persister, progress_tracker)


def get_repo_map_service(
    repo_map_store: RepoMapStore = Depends(get_repo_map_store),
) -> RepoMapService:
    return RepoMapService(repo_map_store)


def get_endpoint_view_service(
    repo_map_service: RepoMapService = Depends(get_repo_map_service),
    render_client: RenderClient = Depends(get_render_client),
) -> EndpointViewService:
    return EndpointViewService(
        repo_map_service, render_client, EndpointCatalog(), EndpointSubgraph()
    )


def get_diagram_edit_service(
    store: DiagramEditStore = Depends(get_diagram_edit_store),
) -> DiagramEditService:
    return DiagramEditService(store)


def get_symbol_context_resolver(
    code_store: CodeStore = Depends(get_code_store),
) -> SymbolContextResolver:
    return SymbolContextResolver(code_store, SourceSlicer())


def get_node_explain_service(
    repo_map_service: RepoMapService = Depends(get_repo_map_service),
    resolver: SymbolContextResolver = Depends(get_symbol_context_resolver),
    explain_client: ExplainClient = Depends(get_explain_client),
    explanation_store: ExplanationStore = Depends(get_explanation_store),
) -> NodeExplainService:
    return NodeExplainService(
        repo_map_service, resolver, explain_client, explanation_store, StepTreeLabeler()
    )


def get_ci_ingest_service(
    analysis_service: AnalysisService = Depends(get_analysis_service),
    repo_map_service: RepoMapService = Depends(get_repo_map_service),
    settings: Settings = Depends(get_settings),
) -> CiIngestService:
    return CiIngestService(
        analysis_service,
        repo_map_service,
        ArchiveExtractor(),
        settings.CI_MAX_UPLOAD_MB * 1024 * 1024,
    )


def get_local_ci_service(
    analysis_service: AnalysisService = Depends(get_analysis_service),
    repo_map_service: RepoMapService = Depends(get_repo_map_service),
    progress_tracker: ProgressTracker = Depends(get_progress_tracker),
) -> LocalCiService:
    return LocalCiService(analysis_service, repo_map_service, progress_tracker)


def get_github_repo_service(
    user_store: UserStore = Depends(get_user_store),
    github_service: GitHubService = Depends(get_github_service),
) -> GitHubRepoService:
    return GitHubRepoService(user_store, github_service)


def get_github_ci_service(
    analysis_service: AnalysisService = Depends(get_analysis_service),
    repo_map_service: RepoMapService = Depends(get_repo_map_service),
    user_store: UserStore = Depends(get_user_store),
    progress_tracker: ProgressTracker = Depends(get_progress_tracker),
) -> GitHubCiService:
    return GitHubCiService(analysis_service, repo_map_service, user_store, progress_tracker)


def get_token_service(
    token_store: AccessTokenStore = Depends(get_token_store),
    hasher: TokenHasher = Depends(get_token_hasher),
) -> TokenService:
    return TokenService(token_store, hasher)
