import json
import re

import anthropic
from prompts.tracer_prompt import TRACER_SYSTEM_PROMPT
from services.tracing.correction_prompt_builder import CorrectionPromptBuilder
from models.evidence_chunk import EvidenceChunk
from services.assembly.graph_validator import GraphValidator
from services.assembly.spec_assembler import SpecAssembler
from shared.models.repo_blueprint import RepoBlueprint

_MODEL = "claude-haiku-4-5-20251001"


class ChunkTracer:
    def __init__(
        self,
        anthropic_client: anthropic.AsyncAnthropic,
        spec_assembler: SpecAssembler,
        graph_validator: GraphValidator,
        correction_builder: CorrectionPromptBuilder,
    ) -> None:
        self._llm = anthropic_client
        self._assembler = spec_assembler
        self._validator = graph_validator
        self._correction_builder = correction_builder

    async def trace_chunk(
        self,
        chunk: EvidenceChunk,
        context: str,
        blueprint: RepoBlueprint,
        architecture_type: str,
    ) -> dict:
        breadcrumb_section = f"PREVIOUS CONTEXT:\n{chunk.breadcrumb}\n\n" if chunk.breadcrumb else ""
        user_prompt = breadcrumb_section + context + "\n\nEVIDENCE BUNDLE:\n" + json.dumps(chunk.evidence)
        messages: list = [{"role": "user", "content": user_prompt}]
        raw = await self._call(messages)
        for attempt in range(1, 3):
            spec = self._assembler.assemble(blueprint, raw, architecture_type)
            validation = self._validator.validate(spec, chunk.evidence)
            if not validation.correctable_warnings or attempt == 2:
                break
            correction = self._correction_builder.build(validation, attempt)
            messages.append({"role": "assistant", "content": [{"type": "text", "text": json.dumps(raw)}]})
            messages.append({"role": "user", "content": correction})
            raw = await self._call(messages)
        return raw

    async def _call(self, messages: list) -> dict:
        response = await self._llm.messages.create(
            model=_MODEL, max_tokens=10000, temperature=0,
            system=TRACER_SYSTEM_PROMPT, messages=messages,
        )
        text = next((b.text for b in response.content if b.type == "text"), "")
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
