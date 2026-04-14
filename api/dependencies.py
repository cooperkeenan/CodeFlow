import inspect
import logging

import httpx
from clients.github_client import GitHubClient
from clients.profiler_client import ProfilerClient
from clients.tracer_client import TracerClient
from clients.render_client import RenderClient
from core.config import Settings, get_settings
from fastapi import Depends, Request
from services.analysis_service import AnalysisService
from services.github_service import GitHubService


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


def get_analysis_service(
    profiler_client: ProfilerClient = Depends(get_profiler_client),
    tracer_client: TracerClient = Depends(get_tracer_client),
    render_client: RenderClient = Depends(get_render_client),
) -> AnalysisService:
    return AnalysisService(profiler_client, tracer_client, render_client)