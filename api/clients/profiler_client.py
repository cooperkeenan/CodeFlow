import logging
import httpx

from models.analysis_model import AnalyseRequest

logger = logging.getLogger(__name__)


class ProfilerClient:
    def __init__(self, http_client: httpx.AsyncClient, base_url: str):
        self._http = http_client
        self._base_url = base_url

    async def profile(self, request: AnalyseRequest) -> dict:
        logger.info("Calling profiler agent for repo: %s", request.repo_name)
        response = await self._http.post(
            f"{self._base_url}/profile",
            json=request.model_dump(),
            timeout=60.0,
        )
        response.raise_for_status()
        return response.json()