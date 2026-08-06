import asyncio
import logging

import httpx

logger = logging.getLogger(__name__)


class ExplainClient:
    def __init__(self, http_client: httpx.AsyncClient, base_url: str):
        self._http = http_client
        self._base_url = base_url

    async def explain(self, payload: dict) -> dict:
        logger.info("Calling explain agent")
        for attempt in range(5):
            try:
                response = await self._http.post(
                    f"{self._base_url}/explain",
                    json=payload,
                    timeout=60.0,
                )
                response.raise_for_status()
                return response.json()
            except httpx.ConnectError:
                if attempt == 4:
                    raise
                await asyncio.sleep(1)
        raise RuntimeError("Explain agent request failed unexpectedly")
