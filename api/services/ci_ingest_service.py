import logging
import tarfile
import tempfile
from pathlib import Path

from fastapi import HTTPException, UploadFile

from models.analysis_model import AnalyseRequest, AnalyseResponse
from services.analysis_service import AnalysisService
from services.archive_extractor import ArchiveExtractor, UnsafeArchiveError
from services.repo_map_service import RepoMapService

logger = logging.getLogger(__name__)


class CiIngestService:
    def __init__(
        self,
        analysis_service: AnalysisService,
        repo_map_service: RepoMapService,
        extractor: ArchiveExtractor,
        max_bytes: int,
    ) -> None:
        self._analysis = analysis_service
        self._repo_maps = repo_map_service
        self._extractor = extractor
        self._max_bytes = max_bytes

    async def ingest(self, user_id: int, repo: str, upload: UploadFile) -> AnalyseResponse:
        data = await upload.read(self._max_bytes + 1)
        if len(data) > self._max_bytes:
            raise HTTPException(status_code=413, detail="Upload exceeds size limit")
        with tempfile.TemporaryDirectory() as temp_dir:
            try:
                self._extractor.extract(data, Path(temp_dir))
            except UnsafeArchiveError as exc:
                raise HTTPException(status_code=400, detail=str(exc)) from exc
            except tarfile.TarError as exc:
                raise HTTPException(status_code=400, detail="Invalid archive") from exc
            result = await self._analysis.analyse(
                AnalyseRequest(repo_name=repo, local_path=temp_dir)
            )
        await self._repo_maps.save(user_id, result, source="ci")
        return result
