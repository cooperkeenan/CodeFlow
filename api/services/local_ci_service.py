import logging
from pathlib import Path

from fastapi import HTTPException

from models.analysis_model import AnalyseRequest, AnalyseResponse
from services.analysis_service import AnalysisService
from services.progress_tracker import ProgressTracker
from services.repo_map_service import RepoMapService

logger = logging.getLogger(__name__)


class LocalCiService:
    def __init__(
        self,
        analysis_service: AnalysisService,
        repo_map_service: RepoMapService,
        progress: ProgressTracker,
    ) -> None:
        self._analysis = analysis_service
        self._repo_maps = repo_map_service
        self._progress = progress

    async def run(self, user_id: int, path: str) -> AnalyseResponse:
        if not path:
            raise HTTPException(status_code=400, detail="No local path configured")
        source = Path(path)
        if not source.is_dir():
            raise HTTPException(status_code=400, detail=f"Local path not found: {path}")
        result = await self._analysis.analyse(
            AnalyseRequest(repo_name=source.name, local_path=str(source))
        )
        await self._repo_maps.save(user_id, result, source="ci-local")
        return result

    async def run_background(self, user_id: int, path: str) -> None:
        try:
            await self.run(user_id, path)
        except Exception as exc:
            logger.warning("Local CI run failed: %s", exc)
            self._progress.fail(str(exc))
