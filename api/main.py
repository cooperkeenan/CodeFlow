import logging
from contextlib import asynccontextmanager

import httpx
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from core.config import get_settings
from routers.analysis import router as analysis_router
from routers.github import router as github_router

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("API Gateway starting up")
    app.state.http_client = httpx.AsyncClient()
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
    app.include_router(analysis_router)
    return app


app = create_app()