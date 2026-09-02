import logging
from contextlib import asynccontextmanager

import httpx
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from gateway.core.config import get_settings
from gateway.routers.auth import router as auth_router
from gateway.routers.ci import router as ci_router
from gateway.routers.diagram_edits import router as diagram_edits_router
from gateway.routers.github import router as github_router
from gateway.routers.repo_maps import router as repo_maps_router
from gateway.routers.tokens import router as tokens_router
from gateway.services.progress_tracker import ProgressTracker

from shared.access_token_store.neon_access_token_store import NeonAccessTokenStore
from shared.code_store.neon_code_store import NeonCodeStore
from shared.diagram_edit_store.neon_diagram_edit_store import NeonDiagramEditStore
from shared.explanation_store.neon_explanation_store import NeonExplanationStore
from shared.repo_map_store.neon_repo_map_store import NeonRepoMapStore
from shared.user_store.neon_user_store import NeonUserStore

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("API Gateway starting up")
    database_url = get_settings().DATABASE_URL
    app.state.http_client = httpx.AsyncClient()
    app.state.code_store = NeonCodeStore(database_url)
    app.state.user_store = NeonUserStore(database_url)
    app.state.token_store = NeonAccessTokenStore(database_url)
    app.state.repo_map_store = NeonRepoMapStore(database_url)
    app.state.explanation_store = NeonExplanationStore(database_url)
    app.state.diagram_edit_store = NeonDiagramEditStore(database_url)
    app.state.progress_tracker = ProgressTracker()
    await app.state.user_store.ensure_schema()
    await app.state.token_store.ensure_schema()
    await app.state.repo_map_store.ensure_schema()
    await app.state.explanation_store.ensure_schema()
    await app.state.diagram_edit_store.ensure_schema()
    yield
    await app.state.http_client.aclose()
    logger.info("API Gateway shut down")


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(title="API Gateway", lifespan=lifespan)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[settings.CORS_ORIGIN],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.include_router(github_router)
    app.include_router(auth_router)
    app.include_router(tokens_router)
    app.include_router(repo_maps_router)
    app.include_router(ci_router)
    app.include_router(diagram_edits_router)
    return app


app = create_app()