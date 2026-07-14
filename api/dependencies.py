import inspect
import logging
from pathlib import Path

import httpx
from clients.github_client import GitHubClient
from clients.layout_client import LayoutClient
from clients.profiler_client import ProfilerClient
from clients.tracer_client import TracerClient
from clients.render_client import RenderClient
from core.config import Settings, get_settings
from fastapi import Depends, Header, HTTPException, Request
from models.auth_model import AuthUser
from services.analysis_service import AnalysisService
from services.progress_tracker import ProgressTracker
from services.archive_extractor import ArchiveExtractor
from services.auth_service import AuthService
from services.ci_ingest_service import CiIngestService
from services.code_read_service import CodeReadService
from services.github_service import GitHubService
from services.local_ci_service import LocalCiService
from services.output_persister import OutputPersister
from services.password_auth_service import PasswordAuthService
from services.password_hasher import PasswordHasher
from services.repo_map_service import RepoMapService
from services.stage_status_service import StageStatusService
from services.token_hasher import TokenHasher
from services.token_service import TokenService
from shared.access_token_store.access_token_store import AccessTokenStore
from shared.code_store.code_store import CodeStore
from shared.repo_map_store.repo_map_store import RepoMapStore
from shared.user_store.user_store import UserStore

_REPO_ROOT = Path(__file__).resolve().parents[1]


logger = logging.getLogger(__name__)


def get_http_client(request: Request) -> httpx.AsyncClient:
    return request.app.state.http_client


def get_github_client(
    http_client: httpx.AsyncClient = Depends(get_http_client),
    settings: Settings = Depends(get_settings),
) -> GitHubClient:
    return GitHubClient(http_client, settings.GITHUB_CLIENT_ID, settings.GITHUB_CLIENT_SECRET)


def get_github_service(
    client: GitHubClient = Depends(get_github_client),
) -> GitHubService:
    return GitHubService(client)


def get_profiler_client(
    http_client: httpx.AsyncClient = Depends(get_http_client),
    settings: Settings = Depends(get_settings),
) -> ProfilerClient:
    return ProfilerClient(http_client, settings.PROFILER_AGENT_URL)


def get_tracer_client(
    http_client: httpx.AsyncClient = Depends(get_http_client),
    settings: Settings = Depends(get_settings),
) -> TracerClient:
    logger.info(
        "Creating TracerClient from %s with trace signature %s",
        inspect.getfile(TracerClient),
        inspect.signature(TracerClient.trace),
    )
    return TracerClient(http_client, settings.TRACER_AGENT_URL)


def get_render_client(
    http_client: httpx.AsyncClient = Depends(get_http_client),
    settings: Settings = Depends(get_settings),
) -> RenderClient:
    return RenderClient(http_client, settings.RENDER_AGENT_URL)


def get_layout_client(
    http_client: httpx.AsyncClient = Depends(get_http_client),
    settings: Settings = Depends(get_settings),
) -> LayoutClient:
    return LayoutClient(http_client, settings.LAYOUT_AGENT_URL)


def get_progress_tracker(request: Request) -> ProgressTracker:
    return request.app.state.progress_tracker


def get_analysis_service(
    profiler_client: ProfilerClient = Depends(get_profiler_client),
    tracer_client: TracerClient = Depends(get_tracer_client),
    render_client: RenderClient = Depends(get_render_client),
    layout_client: LayoutClient = Depends(get_layout_client),
    progress_tracker: ProgressTracker = Depends(get_progress_tracker),
) -> AnalysisService:
    persister = OutputPersister(_REPO_ROOT / "outputs")
    return AnalysisService(profiler_client, tracer_client, render_client, layout_client, persister, progress_tracker)


def get_stage_status_service() -> StageStatusService:
    return StageStatusService()


def get_code_store(request: Request) -> CodeStore:
    return request.app.state.code_store


def get_code_read_service(
    code_store: CodeStore = Depends(get_code_store),
) -> CodeReadService:
    return CodeReadService(code_store)


def get_user_store(request: Request) -> UserStore:
    return request.app.state.user_store


def get_token_store(request: Request) -> AccessTokenStore:
    return request.app.state.token_store


def get_token_hasher() -> TokenHasher:
    return TokenHasher()


def get_auth_service(
    user_store: UserStore = Depends(get_user_store),
    token_store: AccessTokenStore = Depends(get_token_store),
    github_service: GitHubService = Depends(get_github_service),
    hasher: TokenHasher = Depends(get_token_hasher),
) -> AuthService:
    return AuthService(user_store, token_store, github_service, hasher)


def get_password_hasher() -> PasswordHasher:
    return PasswordHasher()


def get_password_auth_service(
    user_store: UserStore = Depends(get_user_store),
    token_store: AccessTokenStore = Depends(get_token_store),
    hasher: TokenHasher = Depends(get_token_hasher),
    password_hasher: PasswordHasher = Depends(get_password_hasher),
) -> PasswordAuthService:
    return PasswordAuthService(user_store, token_store, hasher, password_hasher)


def get_token_service(
    token_store: AccessTokenStore = Depends(get_token_store),
    hasher: TokenHasher = Depends(get_token_hasher),
) -> TokenService:
    return TokenService(token_store, hasher)


def get_repo_map_store(request: Request) -> RepoMapStore:
    return request.app.state.repo_map_store


def get_repo_map_service(
    repo_map_store: RepoMapStore = Depends(get_repo_map_store),
) -> RepoMapService:
    return RepoMapService(repo_map_store)


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


def _bearer_token(authorization: str | None) -> str | None:
    if not authorization or not authorization.lower().startswith("bearer "):
        return None
    return authorization[7:].strip()


async def get_current_user(
    authorization: str | None = Header(default=None),
    auth: AuthService = Depends(get_auth_service),
) -> AuthUser:
    raw = _bearer_token(authorization)
    user = await auth.resolve(raw) if raw else None
    if user is None:
        raise HTTPException(status_code=401, detail="Invalid or missing token")
    return user


async def get_optional_user(
    authorization: str | None = Header(default=None),
    auth: AuthService = Depends(get_auth_service),
) -> AuthUser | None:
    raw = _bearer_token(authorization)
    if not raw:
        return None
    return await auth.resolve(raw)