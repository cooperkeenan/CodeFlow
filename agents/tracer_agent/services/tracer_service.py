import logging

import anthropic
from models.tracer_model import TracerResponse
from prompts.tracer_prompt import TRACER_SYSTEM_PROMPT
from tools.build_call_graph_tool import BUILD_CALL_GRAPH_SCHEMA, BuildCallGraphTool
from tools.fetch_layer_files_tool import FETCH_LAYER_FILES_SCHEMA, FetchLayerFilesTool

from shared.models.tracer_request import TracerRequest

logger = logging.getLogger(__name__)


class TracerService:
    def __init__(
        self,
        fetch_layer_files_tool: FetchLayerFilesTool,
        build_call_graph_tool: BuildCallGraphTool,
        anthropic_client: anthropic.AsyncAnthropic,
    ):
        self._tools = {
            "fetch_layer_files": fetch_layer_files_tool,
            "build_call_graph": build_call_graph_tool,
        }
        self._schemas = [FETCH_LAYER_FILES_SCHEMA, BUILD_CALL_GRAPH_SCHEMA]
        self._llm = anthropic_client

    async def trace(self, request: TracerRequest) -> TracerResponse:
        logger.info("Tracing repo: %s", request.repo_name)

        all_directories = (
            request.layer_hints.presentation
            + request.layer_hints.business
            + request.layer_hints.data
        )

        messages = [
            {
                "role": "user",
                "content": (
                    f"Analyse this repository: {request.repo_name}\n"
                    f"Architecture type: {request.architecture_type}\n"
                    f"Language: {request.language}\n"
                    f"Entry point hint: {request.entry_point_hint}\n"
                    f"Directories to analyse: {all_directories}\n"
                    f"Access token: {request.access_token}"
                ),
            }
        ]

        while True:
            response = await self._llm.messages.create(
                model="claude-haiku-4-5-20251001",
                max_tokens=2000,
                system=TRACER_SYSTEM_PROMPT,
                tools=self._schemas,
                messages=messages,
            )
            logger.info("LLM stop reason: %s", response.stop_reason)

            if response.stop_reason == "end_turn":
                description = next(b.text for b in response.content if b.type == "text")
                logger.info("Tracing complete for %s", request.repo_name)
                return TracerResponse(
                    architecture_type=request.architecture_type,
                    description=description,
                )

            tool_results = []
            for block in response.content:
                if block.type == "tool_use":
                    logger.info("Tool called: %s", block.name)
                    tool_input = block.input
                    if block.name == "fetch_layer_files":
                        tool_input = {
                            "access_token": request.access_token,
                            "repo_name": request.repo_name,
                            "local_path": request.local_path,
                            **block.input,
                        }
                    tool_result = await self._tools[block.name].handle(tool_input)
                    tool_results.append({
                        "type": "tool_result",
                        "tool_use_id": block.id,
                        "content": tool_result,
                    })

            messages.append({"role": "assistant", "content": response.content})
            messages.append({"role": "user", "content": tool_results})
