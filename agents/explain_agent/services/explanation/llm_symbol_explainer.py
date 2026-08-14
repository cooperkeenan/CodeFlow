import json
import logging
import re

import anthropic
from helpers.explanation_validator import ExplanationValidator
from helpers.step_label_validator import StepLabelValidator
from models.explain_model import ExplainRequest, NodeExplanation
from prompts.explain_prompt import EXPLAIN_SYSTEM_PROMPT, build_explain_evidence
from services.explanation.symbol_explainer import SymbolExplainer

logger = logging.getLogger(__name__)
_MODEL = "claude-haiku-4-5-20251001"


class LlmSymbolExplainer:
    def __init__(
        self,
        anthropic_client: anthropic.Anthropic,
        fallback: SymbolExplainer,
        validator: ExplanationValidator,
        step_validator: StepLabelValidator,
    ) -> None:
        self._llm = anthropic_client
        self._fallback = fallback
        self._validator = validator
        self._step_validator = step_validator

    def explain(self, request: ExplainRequest) -> NodeExplanation:
        fallback = self._fallback.explain(request)
        try:
            raw = self._call(request)
            explanation = self._validator.validate(raw, request, fallback)
            step_labels = self._step_validator.validate(raw.get("step_labels"), request.steps)
            return explanation.model_copy(update={"step_labels": step_labels})
        except Exception as exc:
            logger.warning("Symbol explanation fell back for %s: %s", request.focus_fqn, exc)
            return fallback

    def _call(self, request: ExplainRequest) -> dict:
        response = self._llm.messages.create(
            model=_MODEL,
            max_tokens=4000,
            temperature=0,
            system=EXPLAIN_SYSTEM_PROMPT,
            messages=[{"role": "user", "content": build_explain_evidence(request)}],
        )
        text = next((b.text for b in response.content if b.type == "text"), "")
        match = re.search(r"\{.*\}", text, re.DOTALL)
        if not match:
            raise ValueError("LLM did not return valid JSON")
        return json.loads(match.group())
