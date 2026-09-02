import anthropic
import httpx
from fastapi import Depends, Request
from profiler.core.config import Settings, get_settings
from profiler.services.blueprint_validator import BlueprintValidator
from profiler.services.file_tree_service import FileTreeService
from profiler.services.module_detector import ModuleDetector
from profiler.services.profiler_service import ProfilerService
from profiler.services.repo_map_service import RepoMapService


def get_http_client(request: Request) -> httpx.AsyncClient:
    return request.app.state.http_client


def get_file_tree_service(
    http_client: httpx.AsyncClient = Depends(get_http_client),
) -> FileTreeService:
    return FileTreeService(http_client)


def get_anthropic_client(
    settings: Settings = Depends(get_settings),
) -> anthropic.AsyncAnthropic:
    http_client = httpx.AsyncClient(verify=False)
    return anthropic.AsyncAnthropic(
        api_key=settings.ANTHROPIC_API_KEY,
        http_client=http_client,
    )


def get_repo_map_service() -> RepoMapService:
    return RepoMapService(ModuleDetector())


def get_blueprint_validator() -> BlueprintValidator:
    return BlueprintValidator()


def get_profiler_service(
    file_tree_service: FileTreeService = Depends(get_file_tree_service),
    repo_map_service: RepoMapService = Depends(get_repo_map_service),
    blueprint_validator: BlueprintValidator = Depends(get_blueprint_validator),
    anthropic_client: anthropic.AsyncAnthropic = Depends(get_anthropic_client),
) -> ProfilerService:
    return ProfilerService(
        file_tree_service,
        repo_map_service,
        blueprint_validator,
        anthropic_client,
    )
