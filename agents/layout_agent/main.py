import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI

from routers.layout import router as layout_router

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Layout Agent starting up")
    yield
    logger.info("Layout Agent shut down")


def create_app() -> FastAPI:
    app = FastAPI(title="Layout Agent", lifespan=lifespan)
    app.include_router(layout_router)

    @app.get("/health")
    async def health():
        return {"status": "ok"}

    return app


app = create_app()
