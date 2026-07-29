import anthropic
import httpx
from core.config import Settings, get_settings
from fastapi import Depends

from helpers.flow_label_validator import FlowLabelValidator
from services.planning.flow_labeler import FlowLabeler


def get_anthropic_client(
    settings: Settings = Depends(get_settings),
) -> anthropic.AsyncAnthropic:
    http_client = httpx.AsyncClient(verify=False)
    return anthropic.AsyncAnthropic(
        api_key=settings.ANTHROPIC_API_KEY,
        http_client=http_client,
    )


def get_flow_labeler(
    anthropic_client: anthropic.AsyncAnthropic = Depends(get_anthropic_client),
) -> FlowLabeler:
    return FlowLabeler(anthropic_client, FlowLabelValidator())
