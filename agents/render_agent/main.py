import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from render.routers.render import router as render_router

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Render Agent starting up")
    yield
    logger.info("Render Agent shut down")


def create_app() -> FastAPI:
    app = FastAPI(title="Render Agent", lifespan=lifespan)
    app.include_router(render_router)

    @app.get("/health")
    async def health():
        return {"status": "ok"}

    return app


app = create_app()