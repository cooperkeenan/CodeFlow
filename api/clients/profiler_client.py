import asyncio
import logging

import httpx
from models.analysis_model import AnalyseRequest

from shared.models.profiler_response import ProfileResponse

logger = logging.getLogger(__name__)


class ProfilerClient:
    def __init__(self, http_client: httpx.AsyncClient, base_url: str):
        self._http = http_client
        self._base_url = base_url

    async def profile(self, request: AnalyseRequest) -> ProfileResponse:
        logger.info("Calling profiler agent for repo: %s", request.repo_name)
        for attempt in range(5):
            try:
                response = await self._http.post(
                    f"{self._base_url}/profile",
                    json=request.model_dump(),
                    timeout=60.0,
                )
                response.raise_for_status()
                return ProfileResponse.model_validate(response.json())
            except httpx.ConnectError:
                if attempt == 4:
                    raise
                await asyncio.sleep(1)

        raise RuntimeError("Profiler agent request failed unexpectedly")
