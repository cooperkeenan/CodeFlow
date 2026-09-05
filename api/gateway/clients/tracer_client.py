import asyncio
import logging

import httpx

from shared.models.tracer_request import TracerRequest

logger = logging.getLogger(__name__)


class TracerClient:
    def __init__(self, http_client: httpx.AsyncClient, base_url: str):
        self._http = http_client
        self._base_url = base_url

    async def trace(self, request: TracerRequest) -> dict:
        logger.info("Calling tracer agent for: %s", request.repo_name)
        for attempt in range(5):
            try:
                response = await self._http.post(
                    f"{self._base_url}/trace",
                    json=request.model_dump(),
                    timeout=900.0,
                )
                response.raise_for_status()
                return response.json()
            except httpx.ConnectError:
                if attempt == 4:
                    raise
                await asyncio.sleep(1)

        raise RuntimeError("Tracer agent request failed unexpectedly")

    async def progress(self) -> dict | None:
        try:
            response = await self._http.get(f"{self._base_url}/progress", timeout=5.0)
            response.raise_for_status()
            return response.json()
        except (httpx.HTTPError, ValueError):
            return None
