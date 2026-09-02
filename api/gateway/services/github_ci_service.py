import logging

from fastapi import HTTPException
from gateway.models.repo_map_model import AnalyseRequest, AnalyseResponse
from gateway.services.analysis_service import AnalysisService
from gateway.services.progress_tracker import ProgressTracker
from gateway.services.repo_map_service import RepoMapService

from shared.user_store.user_store import UserStore

logger = logging.getLogger(__name__)


class GitHubCiService:
    def __init__(
        self,
        analysis_service: AnalysisService,
        repo_map_service: RepoMapService,
        user_store: UserStore,
        progress: ProgressTracker,
    ) -> None:
        self._analysis = analysis_service
        self._repo_maps = repo_map_service
        self._users = user_store
        self._progress = progress

    async def run(self, user_id: int, repo_name: str) -> AnalyseResponse:
        token = await self._users.get_github_token(user_id)
        if token is None:
            raise HTTPException(status_code=400, detail="GitHub not linked")
        result = await self._analysis.analyse(
            AnalyseRequest(repo_name=repo_name, access_token=token)
        )
        await self._repo_maps.save(user_id, result, source="ci-github")
        return result

    async def run_background(self, user_id: int, repo_name: str) -> None:
        try:
            await self.run(user_id, repo_name)
        except Exception as exc:
            logger.warning("GitHub CI run failed: %s", exc)
            self._progress.fail(str(exc))
