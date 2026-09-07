import json
import logging
import re

import anthropic
from explain.helpers.contract_validator import ContractValidator
from explain.models.contract_model import ContractRequest
from explain.prompts.contract_prompt import (
    CONTRACT_SYSTEM_PROMPT,
    build_contract_evidence,
)
from explain.services.contract.contract_writer import ContractWriter

from shared.models.endpoint_contract import EndpointContract

logger = logging.getLogger(__name__)
_MODEL = "claude-haiku-4-5-20251001"


class LlmContractWriter:
    def __init__(
        self,
        anthropic_client: anthropic.Anthropic,
        fallback: ContractWriter,
        validator: ContractValidator,
    ) -> None:
        self._llm = anthropic_client
        self._fallback = fallback
        self._validator = validator

    def write(self, request: ContractRequest) -> EndpointContract:
        try:
            raw = self._call(request)
            raw.pop("generated", None)
            contract = EndpointContract(**raw, generated=True)
            if not self._validator.validate(contract, request):
                raise ValueError("LLM contract failed validation")
            return contract
        except Exception as exc:
            logger.warning("Contract write fell back for %s: %s", request.entry_id, exc)
            return self._fallback.write(request)

    def _call(self, request: ContractRequest) -> dict:
        response = self._llm.messages.create(
            model=_MODEL,
            max_tokens=4000,
            system=CONTRACT_SYSTEM_PROMPT,
            messages=[{"role": "user", "content": build_contract_evidence(request)}],
        )
        text = next((b.text for b in response.content if b.type == "text"), "")
        match = re.search(r"\{.*\}", text, re.DOTALL)
        if not match:
            raise ValueError("LLM did not return valid JSON")
        return json.loads(match.group())
