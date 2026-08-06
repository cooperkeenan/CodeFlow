import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI

from routers.explain import router as explain_router

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Explain Agent starting up")
    yield
    logger.info("Explain Agent shut down")


def create_app() -> FastAPI:
    app = FastAPI(title="Explain Agent", lifespan=lifespan)
    app.include_router(explain_router)

    @app.get("/health")
    async def health():
        return {"status": "ok"}

    return app


app = create_app()
