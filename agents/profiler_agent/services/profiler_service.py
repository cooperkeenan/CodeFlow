import json
import logging
import re

import anthropic
from models.profiler_model import ProfileRequest, ProfileResponse
from models.repo_skeleton import RepoSkeleton
from prompts.profiler_prompt import PROFILER_SYSTEM_PROMPT
from services.blueprint_validator import BlueprintValidator
from services.file_tree_service import FileTreeService
from services.repo_map_service import RepoMapService

logger = logging.getLogger(__name__)


class ProfilerService:
    def __init__(
        self,
        file_tree_service: FileTreeService,
        repo_map_service: RepoMapService,
        blueprint_validator: BlueprintValidator,
        anthropic_client: anthropic.AsyncAnthropic,
    ):
        self._files = file_tree_service
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
        zone_count = sum(len(m.zones) for m in blueprint.modules)
        logger.info(
            "Blueprint: arch=%s lang=%s modules=%d zones=%d",
            blueprint.architecture_type,
            blueprint.language,
            len(blueprint.modules),
            zone_count,
        )
        for m in blueprint.modules:
            logger.info("  module %-20s zones=%s", m.name, [z.name for z in m.zones])
        return blueprint

    def _target(self, request: ProfileRequest) -> dict:
        if request.local_path:
            return {"local_path": request.local_path}
        return {"access_token": request.access_token, "repo_name": request.repo_name}

    async def _fetch_paths(self, request: ProfileRequest) -> list[str]:
        return await self._files.get_tree(**self._target(request))

    async def _fetch_manifests(self, request: ProfileRequest, paths: list[str]) -> dict:
        return await self._files.get_manifests(**self._target(request), paths=paths)

    async def _label(self, user_prompt: str) -> dict:
        response = await self._llm.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=4000,
            temperature=0,
            system=PROFILER_SYSTEM_PROMPT,
            messages=[{"role": "user", "content": user_prompt}],
        )
        text = next((b.text for b in response.content if b.type == "text"), "")
        logger.info("profiler raw output: %s", text)
        match = re.search(r"\{.*\}", text, re.DOTALL)
        if not match:
            raise ValueError("LLM did not return valid JSON")
        try:
            return json.loads(match.group())
        except json.JSONDecodeError as exc:
            raise ValueError(f"LLM returned malformed JSON: {exc}") from exc

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
