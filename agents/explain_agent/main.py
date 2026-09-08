import logging
from contextlib import asynccontextmanager

from explain.routers.contract import router as contract_router
from explain.routers.explain import router as explain_router
from fastapi import FastAPI

from shared.run_log.setup import configure_logging

configure_logging("explain")

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Explain Agent starting up")
    yield
    logger.info("Explain Agent shut down")


def create_app() -> FastAPI:
    app = FastAPI(title="Explain Agent", lifespan=lifespan)
    app.include_router(explain_router)
    app.include_router(contract_router)

    @app.get("/health")
    async def health():
        return {"status": "ok"}

    return app


app = create_app()
