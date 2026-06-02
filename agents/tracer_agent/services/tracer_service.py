import json
import logging
import re

import anthropic
from anthropic.types import MessageParam
from models.tracer_model import TracerResponse
from prompts.tracer_prompt import TRACER_SYSTEM_PROMPT
from services.correction_prompt_builder import CorrectionPromptBuilder
from services.graph_validator import GraphValidator
from services.spec_assembler import SpecAssembler
from tools.build_call_graph_tool import BuildCallGraphTool
from tools.build_evidence_tool import BuildEvidenceTool
from tools.fetch_layer_files_tool import FetchLayerFilesTool

from shared.models.diagram_spec import DiagramSpec
from shared.models.repo_blueprint import RepoBlueprint
from shared.models.tracer_request import TracerRequest

logger = logging.getLogger(__name__)

_MODEL = "claude-haiku-4-5-20251001"


class TracerService:
    def __init__(
        self,
        fetch_layer_files_tool: FetchLayerFilesTool,
        build_call_graph_tool: BuildCallGraphTool,
        build_evidence_tool: BuildEvidenceTool,
        spec_assembler: SpecAssembler,
        anthropic_client: anthropic.AsyncAnthropic,
    ):
        self._fetch = fetch_layer_files_tool
        self._call_graph = build_call_graph_tool
        self._evidence_tool = build_evidence_tool
        self._assembler = spec_assembler
        self._llm = anthropic_client

    async def trace(self, request: TracerRequest) -> TracerResponse:
        logger.info("Tracing repo: %s", request.repo_name)
        evidence = await self._gather_evidence(request)
        messages: list[MessageParam] = [
            {"role": "user", "content": self._user_prompt(request.blueprint, evidence)}
        ]
        raw = await self._call(messages)
        spec = self._assembler.assemble(request.blueprint, raw, request.architecture_type)
        spec = await self._correction_loop(spec, raw, messages, evidence, request)
        component_count = sum(len(comps) for m in spec.modules for comps in m.zones.values())
        edge_types: dict[str, int] = {}
        for e in spec.edges:
            edge_types[e.edge_type] = edge_types.get(e.edge_type, 0) + 1
        logger.info(
            "Trace: modules=%d components=%d edges=%d %s",
            len(spec.modules),
            component_count,
            len(spec.edges),
            " ".join(f"{k}={v}" for k, v in sorted(edge_types.items())),
        )
        return TracerResponse(architecture_type=request.architecture_type, diagram_spec=spec)

    async def _gather_evidence(self, request: TracerRequest) -> dict:
        directories = self._minimal_dirs(request.blueprint)
        fetch = json.loads(await self._fetch.handle({
            "directories": directories,
            "access_token": request.access_token,
            "repo_name": request.repo_name,
            "local_path": request.local_path,
        }))
        if "error" in fetch:
            raise ValueError(f"fetch_layer_files failed: {fetch['error']}")
        args = {"temp_dir": fetch["temp_dir"], "file_paths": fetch["file_paths"]}
        call_graph = json.loads(await self._call_graph.handle(
            {**args, "entry_point_hint": request.entry_point_hint}
        ))
        evidence = json.loads(await self._evidence_tool.handle({**args, "call_graph": call_graph}))
        return {} if "error" in evidence else evidence

    def _minimal_dirs(self, blueprint: RepoBlueprint) -> list[str]:
        dirs = sorted({d for m in blueprint.modules for z in m.zones for d in z.directories})
        return [d for d in dirs if not any(o != d and d.startswith(o) for o in dirs)]

    async def _call(self, messages: list) -> dict:
        response = await self._llm.messages.create(
            model=_MODEL, max_tokens=10000, temperature=0,
            system=TRACER_SYSTEM_PROMPT, messages=messages,
        )
        text = next((b.text for b in response.content if b.type == "text"), "")
        logger.info("tracer raw output: %s", text)
        match = re.search(r"\{.*\}", text, re.DOTALL)
        if not match:
            raise ValueError("LLM did not return valid JSON")
        return self._sanitise(json.loads(match.group()))

    def _sanitise(self, raw: dict) -> dict:
        for c in raw.get("components", []):
            io = c.get("io") if isinstance(c, dict) else None
            if isinstance(io, dict):
                io["inputs"] = [v for v in io.get("inputs", []) if v]
                io["outputs"] = [v for v in io.get("outputs", []) if v]
        raw["edges"] = [
            e for e in raw.get("edges", [])
            if isinstance(e, dict) and e.get("source") and e.get("target")
        ]
        return raw

    async def _correction_loop(
        self, spec: DiagramSpec, raw: dict, messages: list, evidence: dict, request: TracerRequest
    ) -> DiagramSpec:
        for attempt in range(1, 4):
            validation = GraphValidator().validate(spec, evidence)
            spec = validation.fixed_spec
            for msg in validation.errors + validation.warnings:
                logger.warning("Validator: %s", msg)
            if not validation.correctable_warnings or attempt == 3:
                return spec
            correction = CorrectionPromptBuilder().build(validation, attempt)
            messages.append({"role": "assistant", "content": [{"type": "text", "text": json.dumps(raw)}]})
            messages.append({"role": "user", "content": correction})
            raw = await self._call(messages)
            spec = self._assembler.assemble(request.blueprint, raw, request.architecture_type)
        return spec

    def _user_prompt(self, blueprint: RepoBlueprint, evidence: dict) -> str:
        structure = "\n".join(
            f"{m.name} ({m.root_path}): zones {[z.name for z in m.zones]}"
            for m in blueprint.modules
        )
        return (
            "BLUEPRINT MODULES (context only — placement is automatic by file_path):\n"
            + structure
            + "\n\nEVIDENCE BUNDLE:\n"
            + json.dumps(evidence)
        )
