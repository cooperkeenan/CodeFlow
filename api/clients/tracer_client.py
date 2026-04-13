import logging

import httpx
from models.analysis_model import AnalyseRequest

logger = logging.getLogger(__name__)


class TracerClient:
    def __init__(self, http_client: httpx.AsyncClient, base_url: str):
        self._http = http_client
        self._base_url = base_url

    async def trace(self, request: AnalyseRequest, profile: dict) -> dict:
        logger.info("Calling tracer agent for: %s", request.repo_name)
        response = await self._http.post(
            f"{self._base_url}/trace",
            json={
                "repo_name": request.repo_name,
                "access_token": request.access_token,
                "local_path": request.local_path,
                "architecture_type": profile["architecture_type"],
                "language": profile["language"],
                "entry_point_hint": profile["entry_point_hint"],
                "layer_hints": profile["layer_hints"],
            },
            timeout=120.0,
        )
        response.raise_for_status()
        return response.json()