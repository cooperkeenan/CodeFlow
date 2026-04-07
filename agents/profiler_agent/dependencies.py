import anthropic
import httpx
from fastapi import Depends, Request

from core.config import Settings, get_settings
from services.file_tree_service import FileTreeService
from services.profiler_service import ProfilerService
from tools.get_file_tree_tool import GetFileTreeTool
from tools.get_manifest_tool import GetManifestFilesTool


def get_http_client(request: Request) -> httpx.AsyncClient:
    return request.app.state.http_client


def get_file_tree_service(
    http_client: httpx.AsyncClient = Depends(get_http_client),
) -> FileTreeService:
    return FileTreeService(http_client)


def get_file_tree_tool(
    service: FileTreeService = Depends(get_file_tree_service),
) -> GetFileTreeTool:
    return GetFileTreeTool(service)


def get_manifest_files_tool(
    service: FileTreeService = Depends(get_file_tree_service),
) -> GetManifestFilesTool:
    return GetManifestFilesTool(service)


def get_anthropic_client(
    settings: Settings = Depends(get_settings),
) -> anthropic.AsyncAnthropic:
    return anthropic.AsyncAnthropic(api_key=settings.ANTHROPIC_API_KEY)


def get_profiler_service(
    get_file_tree_tool: GetFileTreeTool = Depends(get_file_tree_tool),
    get_manifest_files_tool: GetManifestFilesTool = Depends(get_manifest_files_tool),
    anthropic_client: anthropic.AsyncAnthropic = Depends(get_anthropic_client),
) -> ProfilerService:
    return ProfilerService(get_file_tree_tool, get_manifest_files_tool, anthropic_client)