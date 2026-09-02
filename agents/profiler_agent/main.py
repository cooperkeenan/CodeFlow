import logging
from contextlib import asynccontextmanager

import httpx
from fastapi import FastAPI
from profiler.routers.profiler import router as profiler_router

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Profiler Agent starting up")
    app.state.http_client = httpx.AsyncClient()
    yield
    await app.state.http_client.aclose()
    logger.info("Profiler Agent shut down")


def create_app() -> FastAPI:
    app = FastAPI(title="Profiler Agent", lifespan=lifespan)
    app.include_router(profiler_router)
    return app


app = create_app()