import json
import logging
import re

import anthropic
from models.profiler_model import LayerHints, ProfileRequest, ProfileResponse
from prompts.profiler_prompt import PROFILER_SYSTEM_PROMPT
from tools.get_file_tree_tool import GET_FILE_TREE_SCHEMA, GetFileTreeTool
from tools.get_manifest_tool import (
    GET_MANIFEST_FILES_SCHEMA,
    GetManifestFilesTool,
)

logger = logging.getLogger(__name__)


class ProfilerService:
    def __init__(
        self,
        get_file_tree_tool: GetFileTreeTool,
        get_manifest_files_tool: GetManifestFilesTool,
        anthropic_client: anthropic.AsyncAnthropic,
    ):
        self._tools = {
            "get_file_tree": get_file_tree_tool,
            "get_manifest_files": get_manifest_files_tool,
        }
        self._schemas = [GET_FILE_TREE_SCHEMA, GET_MANIFEST_FILES_SCHEMA]
        self._llm = anthropic_client

    async def profile(self, request: ProfileRequest) -> ProfileResponse:
        logger.info("Profiling repo: %s", request.repo_name)

        if request.local_path:
            user_content = f"Classify this local repository at path: {request.local_path}"
        else:
            user_content = (
                f"Classify this repository: {request.repo_name}. "
                f"Access token: {request.access_token}"
            )

        messages = [{"role": "user", "content": user_content}]

        while True:
            response = await self._llm.messages.create(
                model="claude-haiku-4-5-20251001",
                max_tokens=1000,
                system=PROFILER_SYSTEM_PROMPT,
                tools=self._schemas,
                messages=messages,
            )
            logger.info("LLM stop reason: %s", response.stop_reason)

            if response.stop_reason == "end_turn":
                text = next(b.text for b in response.content if b.type == "text")
                logger.info("Raw LLM response: %s", text)

                match = re.search(r"\{.*\}", text, re.DOTALL)
                if not match:
                    raise ValueError("LLM did not return valid JSON")

                result = json.loads(match.group())
                logger.info(
                    "Classification complete: %s / %s",
                    result["architecture_type"],
                    result["framework"],
                )
                return ProfileResponse(
                    architecture_type=result["architecture_type"],
                    language=result["language"],
                    framework=result["framework"],
                    patterns=result["patterns"],
                    entry_point_hint=result["entry_point_hint"],
                    layer_hints=LayerHints(**result["layer_hints"]),
                )

            tool_results = []
            for block in response.content:
                if block.type == "tool_use":
                    logger.info("Tool called: %s", block.name)
                    tool_result = await self._tools[block.name].handle(block.input)
                    tool_results.append({
                        "type": "tool_result",
                        "tool_use_id": block.id,
                        "content": tool_result,
                    })

            messages.append({"role": "assistant", "content": response.content})
            messages.append({"role": "user", "content": tool_results})