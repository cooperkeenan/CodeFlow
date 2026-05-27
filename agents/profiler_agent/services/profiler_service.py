import json
import logging
import re

import anthropic
from models.profiler_model import ProfileRequest, ProfileResponse
from models.repo_skeleton import RepoSkeleton
from prompts.profiler_prompt import PROFILER_SYSTEM_PROMPT
from services.blueprint_validator import BlueprintValidator
from services.repo_map_service import RepoMapService
from tools.get_file_tree_tool import GetFileTreeTool
from tools.get_manifest_tool import GetManifestFilesTool

logger = logging.getLogger(__name__)


class ProfilerService:
    def __init__(
        self,
        get_file_tree_tool: GetFileTreeTool,
        get_manifest_files_tool: GetManifestFilesTool,
        repo_map_service: RepoMapService,
        blueprint_validator: BlueprintValidator,
        anthropic_client: anthropic.AsyncAnthropic,
    ):
        self._file_tree = get_file_tree_tool
        self._manifests = get_manifest_files_tool
        self._repo_map = repo_map_service
        self._validator = blueprint_validator
        self._llm = anthropic_client

    async def profile(self, request: ProfileRequest) -> ProfileResponse:
        logger.info("Profiling repo: %s", request.repo_name)
        paths = await self._fetch_paths(request)
        manifests = await self._fetch_manifests(request, paths)
        skeleton = self._repo_map.build(paths, request.repo_name)
        raw = await self._label(self._user_prompt(skeleton, manifests))
        blueprint = self._validator.validate(raw, skeleton)
        logger.info(
            "Blueprint complete: %s, %d modules",
            blueprint.architecture_type, len(blueprint.modules),
        )
        return blueprint

    def _target(self, request: ProfileRequest) -> dict:
        if request.local_path:
            return {"local_path": request.local_path}
        return {"access_token": request.access_token, "repo_name": request.repo_name}

    async def _fetch_paths(self, request: ProfileRequest) -> list[str]:
        result = json.loads(await self._file_tree.handle(self._target(request)))
        if isinstance(result, dict) and "error" in result:
            raise ValueError(f"get_file_tree failed: {result['error']}")
        return result

    async def _fetch_manifests(self, request: ProfileRequest, paths: list[str]) -> dict:
        result = json.loads(await self._manifests.handle({**self._target(request), "paths": paths}))
        return {} if isinstance(result, dict) and "error" in result else result

    async def _label(self, user_prompt: str) -> dict:
        response = await self._llm.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=4000,
            temperature=0,
            system=PROFILER_SYSTEM_PROMPT,
            messages=[{"role": "user", "content": user_prompt}],
        )
        text = next((b.text for b in response.content if b.type == "text"), "")
        match = re.search(r"\{.*\}", text, re.DOTALL)
        if not match:
            raise ValueError("LLM did not return valid JSON")
        return json.loads(match.group())

    def _user_prompt(self, skeleton: RepoSkeleton, manifests: dict) -> str:
        lines = ["MODULE/DIRECTORY SKELETON (fixed — label only, do not change):", ""]
        for module in skeleton.modules:
            lines.append(f"- module: {module.name}  (root_path: {module.root_path or '(repo root)'})")
            for d in module.directories:
                samples = ", ".join(d.sample_files)
                lines.append(f"    {d.path or '(root)'}  [{d.file_count} files: {samples}]")
        lines += ["", "MANIFEST FILES:"]
        for path, content in manifests.items():
            lines.append(f"--- {path} ---\n{content[:1500]}")
        return "\n".join(lines)
