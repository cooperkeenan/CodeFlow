import logging
from pathlib import Path

from fastapi import HTTPException
from gateway.models.repo_map_model import AnalyseRequest, AnalyseResponse
from gateway.services.analysis_service import AnalysisService
from gateway.services.failure_message import describe_failure
from gateway.services.progress_tracker import ProgressTracker
from gateway.services.repo_map_service import RepoMapService

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
        self._progress.step(f"local CI from {source}")
        result = await self._analysis.analyse(
            AnalyseRequest(repo_name=source.name, local_path=str(source))
        )
        self._progress.begin("save", "Writing the repo map to the database")
        await self._repo_maps.save(user_id, result, source="ci-local")
        self._progress.complete("save", f"saved repo map for {source.name}")
        return result

    async def run_background(self, user_id: int, path: str) -> None:
        try:
            await self.run(user_id, path)
        except Exception as exc:
            logger.exception("Local CI run failed")
            self._progress.fail(describe_failure(exc))
