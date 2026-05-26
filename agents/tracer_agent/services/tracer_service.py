import json
import logging
import re

import anthropic
from anthropic.types import MessageParam, ToolResultBlockParam
from models.tracer_model import TracerResponse
from prompts.tracer_prompt import TRACER_SYSTEM_PROMPT
from services.correction_prompt_builder import CorrectionPromptBuilder
from services.graph_validator import GraphValidator
from tools.build_call_graph_tool import BUILD_CALL_GRAPH_SCHEMA, BuildCallGraphTool
from tools.build_evidence_tool import BUILD_EVIDENCE_SCHEMA, BuildEvidenceTool
from tools.fetch_layer_files_tool import FETCH_LAYER_FILES_SCHEMA, FetchLayerFilesTool
from tools.get_diagram_template_tool import (
    GET_DIAGRAM_TEMPLATE_SCHEMA,
    GetDiagramTemplateTool,
)

from shared.models.diagram_spec import DiagramSpec
from shared.models.tracer_request import TracerRequest

logger = logging.getLogger(__name__)


class TracerService:
    def __init__(
        self,
        fetch_layer_files_tool: FetchLayerFilesTool,
        build_call_graph_tool: BuildCallGraphTool,
        diagram_template_tool: GetDiagramTemplateTool,
        build_evidence_tool: BuildEvidenceTool,
        anthropic_client: anthropic.AsyncAnthropic,
    ):
        self._tools = {
            "fetch_layer_files": fetch_layer_files_tool,
            "build_call_graph": build_call_graph_tool,
            "get_diagram_template": diagram_template_tool,
            "build_evidence": build_evidence_tool,
        }
        self._schemas = [
            FETCH_LAYER_FILES_SCHEMA,
            BUILD_CALL_GRAPH_SCHEMA,
            GET_DIAGRAM_TEMPLATE_SCHEMA,
            BUILD_EVIDENCE_SCHEMA,
        ]
        self._llm = anthropic_client
        self._evidence: dict = {}

    def _sanitise_io(self, result: dict) -> dict:
        for component in (
            c for layer in result.get("layers", {}).values() for c in layer
            if isinstance(c, dict) and "io" in c and isinstance(c["io"], dict)
        ):
            io = component["io"]
            io["inputs"] = [v for v in io.get("inputs", []) if v is not None]
            io["outputs"] = [v for v in io.get("outputs", []) if v is not None]
        return result

    def _parse_spec(self, raw: dict, request: TracerRequest) -> DiagramSpec:
        raw["architecture_type"] = request.architecture_type
        return DiagramSpec.model_validate(self._sanitise_io(raw))

    async def _correction_loop(
        self, raw: dict, messages: list, request: TracerRequest
    ) -> DiagramSpec:
        spec = self._parse_spec(raw, request)
        for attempt in range(1, 4):
            validation = GraphValidator().validate(spec, self._evidence)
            spec = validation.fixed_spec
            for msg in validation.errors + validation.warnings:
                logger.warning("Validator: %s", msg)
            if not validation.correctable_warnings or attempt == 3:
                if attempt == 3 and validation.correctable_warnings:
                    logger.warning("Max correction attempts reached with %d unresolved warnings", len(validation.correctable_warnings))
                elif attempt > 1:
                    logger.info("Correction attempt %d resolved all issues", attempt - 1)
                return spec
            correction = CorrectionPromptBuilder().build(validation, attempt)
            logger.info("Correction attempt %d: %s", attempt, correction)
            messages.append({"role": "assistant", "content": [{"type": "text", "text": f"```json\n{spec.model_dump_json()}\n```"}]})
            messages.append({"role": "user", "content": correction})
            response = await self._llm.messages.create(model="claude-haiku-4-5-20251001", max_tokens=10000, system=TRACER_SYSTEM_PROMPT, tools=self._schemas, messages=messages)
            text = next((b.text for b in response.content if b.type == "text"), None)
            match = re.search(r"\{.*\}", text, re.DOTALL) if text else None
            if not match:
                logger.warning("Correction attempt %d returned no JSON", attempt)
                return spec
            spec = self._parse_spec(json.loads(match.group()), request)
        return spec

    async def _handle_tool_calls(self, response, request: TracerRequest) -> list[ToolResultBlockParam]:
        tool_results: list[ToolResultBlockParam] = []
        for block in response.content:
            if block.type != "tool_use":
                continue
            logger.info("Tool called: %s", block.name)
            tool_input = dict(block.input)
            if block.name == "fetch_layer_files":
                tool_input = {**block.input, "access_token": request.access_token, "repo_name": request.repo_name, "local_path": request.local_path}
            elif block.name == "build_call_graph":
                tool_input = {**block.input, "entry_point_hint": request.entry_point_hint}
            tool_result = await self._tools[block.name].handle(tool_input)
            if block.name == "build_evidence":
                parsed = json.loads(tool_result)
                if "error" not in parsed:
                    self._evidence = parsed
            tool_results.append(ToolResultBlockParam(type="tool_result", tool_use_id=block.id, content=tool_result))
        return tool_results

    async def trace(self, request: TracerRequest) -> TracerResponse:
        logger.info("Tracing repo: %s", request.repo_name)
        all_directories = (
            request.layer_hints.presentation
            + request.layer_hints.business
            + request.layer_hints.data
        )
        messages: list[MessageParam] = [{"role": "user", "content": (
            f"Analyse this repository: {request.repo_name}\n"
            f"Architecture type: {request.architecture_type}\n"
            f"Language: {request.language}\n"
            f"Entry point hint: {request.entry_point_hint}\n"
            f"Directories to analyse: {all_directories}\n"
            f"Access token: {request.access_token}"
        )}]
        while True:
            response = await self._llm.messages.create(model="claude-haiku-4-5-20251001", max_tokens=10000, system=TRACER_SYSTEM_PROMPT, tools=self._schemas, messages=messages)
            logger.info("LLM stop reason: %s", response.stop_reason)
            if response.stop_reason == "end_turn":
                text = next(b.text for b in response.content if b.type == "text")
                logger.info("Raw LLM response: %s", text)
                match = re.search(r"\{.*\}", text, re.DOTALL)
                if not match:
                    raise ValueError("LLM did not return valid JSON")
                diagram_spec = await self._correction_loop(json.loads(match.group()), messages, request)
                logger.info("Tracing complete for %s", request.repo_name)
                return TracerResponse(architecture_type=request.architecture_type, diagram_spec=diagram_spec)
            tool_results = await self._handle_tool_calls(response, request)
            messages.append({"role": "assistant", "content": response.content})  # type: ignore[arg-type]
            messages.append({"role": "user", "content": tool_results})
