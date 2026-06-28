import logging
from contextlib import asynccontextmanager

import httpx
from fastapi import FastAPI

from routers.tracer import router as tracer_router

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Tracer Agent starting up")
    app.state.http_client = httpx.AsyncClient()
    yield
    await app.state.http_client.aclose()
    logger.info("Tracer Agent shut down")


def create_app() -> FastAPI:
    app = FastAPI(title="Tracer Agent", lifespan=lifespan)
    app.include_router(tracer_router)
    return app


app = create_app()