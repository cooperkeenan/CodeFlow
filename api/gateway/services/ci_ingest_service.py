import base64
import logging
import tarfile
import tempfile
from pathlib import Path

from fastapi import HTTPException, UploadFile
from gateway.models.repo_map_model import AnalyseRequest, AnalyseResponse
from gateway.services.analysis_service import AnalysisService
from gateway.services.archive_extractor import ArchiveExtractor, UnsafeArchiveError
from gateway.services.progress_tracker import ProgressTracker
from gateway.services.repo_map_service import RepoMapService

logger = logging.getLogger(__name__)


class CiIngestService:
    def __init__(
        self,
        analysis_service: AnalysisService,
        repo_map_service: RepoMapService,
        extractor: ArchiveExtractor,
        max_bytes: int,
        progress: ProgressTracker,
    ) -> None:
        self._analysis = analysis_service
        self._repo_maps = repo_map_service
        self._extractor = extractor
        self._max_bytes = max_bytes
        self._progress = progress

    async def ingest(self, user_id: int, repo: str, upload: UploadFile) -> AnalyseResponse:
        self._progress.start(repo)
        data = await upload.read(self._max_bytes + 1)
        if len(data) > self._max_bytes:
            raise HTTPException(status_code=413, detail="Upload exceeds size limit")
        with tempfile.TemporaryDirectory() as temp_dir:
            try:
                self._progress.step(f"extracting {len(data) // 1024} KiB archive")
                self._extractor.extract(data, Path(temp_dir))
            except UnsafeArchiveError as exc:
                raise HTTPException(status_code=400, detail=str(exc)) from exc
            except tarfile.TarError as exc:
                raise HTTPException(status_code=400, detail="Invalid archive") from exc
            result = await self._analysis.analyse(
                AnalyseRequest(
                    repo_name=repo,
                    local_path=temp_dir,
                    archive_gz=base64.b64encode(data).decode(),
                )
            )
        self._progress.begin("save", "Writing the repo map to the database")
        await self._repo_maps.save(user_id, result, source="ci")
        self._progress.complete("save", f"saved repo map for {repo}")
        return result
