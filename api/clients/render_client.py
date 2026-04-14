import asyncio
import logging

import httpx

from shared.models.diagram_spec import DiagramSpec

logger = logging.getLogger(__name__)


class RenderClient:
    def __init__(self, http_client: httpx.AsyncClient, base_url: str):
        self._http = http_client
        self._base_url = base_url

    async def render(self, architecture_type: str, diagram_spec: dict) -> str:
        logger.info("Calling render agent")
        for attempt in range(5):
            try:
                response = await self._http.post(
                    f"{self._base_url}/render",
                    json={
                        "architecture_type": architecture_type,
                        "diagram_spec": diagram_spec,
                    },
                    timeout=30.0,
                )
                response.raise_for_status()
                return response.json()["mermaid"]
            except httpx.ConnectError:
                if attempt == 4:
                    raise
                await asyncio.sleep(1)
        raise RuntimeError("Render agent request failed unexpectedly")