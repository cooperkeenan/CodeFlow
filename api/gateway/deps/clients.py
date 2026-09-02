import inspect
import logging

import httpx
from fastapi import Depends, Request

from gateway.clients.explain_client import ExplainClient
from gateway.clients.github_client import GitHubClient
from gateway.clients.profiler_client import ProfilerClient
from gateway.clients.render_client import RenderClient
from gateway.clients.tracer_client import TracerClient
from gateway.core.config import Settings, get_settings
from gateway.services.github_service import GitHubService

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


def get_explain_client(
    http_client: httpx.AsyncClient = Depends(get_http_client),
    settings: Settings = Depends(get_settings),
) -> ExplainClient:
    return ExplainClient(http_client, settings.EXPLAIN_AGENT_URL)
