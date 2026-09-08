import logging
from contextlib import asynccontextmanager

import httpx
from fastapi import FastAPI
from tracer.routers.tracer import router as tracer_router
from tracer.services.analysis.stage_reporter import StageReporter

from shared.run_log.handler import EventLogHandler
from shared.run_log.setup import configure_logging

configure_logging("tracer")

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Tracer Agent starting up")
    app.state.http_client = httpx.AsyncClient()
    app.state.stage_reporter = StageReporter()
    logging.getLogger().addHandler(EventLogHandler(app.state.stage_reporter.sink, "tracer"))
    yield
    await app.state.http_client.aclose()
    logger.info("Tracer Agent shut down")


def create_app() -> FastAPI:
    app = FastAPI(title="Tracer Agent", lifespan=lifespan)
    app.include_router(tracer_router)
    return app


app = create_app()