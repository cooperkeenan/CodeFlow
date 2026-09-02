import base64
import io
import logging
import shutil
import tarfile
import tempfile
from pathlib import Path

from tracer.services.evidence.file_inclusion import is_included
from tracer.services.evidence.github_file_fetcher import GitHubFileFetcher

logger = logging.getLogger(__name__)


class FileFetchService:
    def __init__(self, github_fetcher: GitHubFileFetcher) -> None:
        self._github = github_fetcher

    async def fetch_files(
        self,
        *,
        repo_name: str | None = None,
        access_token: str | None = None,
        local_path: str | None = None,
        archive_gz: str | None = None,
        directories: list[str],
    ) -> tuple[str, list[str]]:
        if local_path and Path(local_path).exists():
            return self._copy_local_files(local_path, directories)
        if archive_gz:
            return self._extract_archive(archive_gz, directories)
        if not access_token or not repo_name:
            raise ValueError(
                "fetch_files requires local_path, archive_gz, or "
                "both access_token and repo_name for GitHub repos"
            )
        return await self._github.fetch_files_to_temp(access_token, repo_name, directories)

    def _extract_archive(self, archive_gz: str, directories: list[str]) -> tuple[str, list[str]]:
        raw = base64.b64decode(archive_gz)
        temp_dir = tempfile.mkdtemp()
        with tarfile.open(fileobj=io.BytesIO(raw), mode="r:gz") as tf:
            tf.extractall(temp_dir)
        if directories:
            return self._copy_local_files(temp_dir, directories)
        return self._scan_all(temp_dir)

    def _scan_all(self, root: str) -> tuple[str, list[str]]:
        temp_dir = tempfile.mkdtemp()
        written: list[str] = []
        for file_path in Path(root).rglob("*.py"):
            if not is_included(file_path):
                continue
            dest = Path(temp_dir) / file_path.relative_to(root)
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(file_path, dest)
            written.append(str(dest))
        logger.info("Scanned all: %d files", len(written))
        return temp_dir, written

    def _copy_local_files(
        self,
        local_path: str,
        directories: list[str],
    ) -> tuple[str, list[str]]:
        root = Path(local_path)
        temp_dir = tempfile.mkdtemp()
        written_files: list[str] = []
        for directory in directories:
            source_path = root / directory.rstrip("/")
            if not source_path.exists():
                logger.warning("Path not found: %s", source_path)
                continue
            candidates = [source_path] if source_path.is_file() else list(source_path.rglob("*.py"))
            for file_path in candidates:
                if not is_included(file_path):
                    continue
                dest = Path(temp_dir) / file_path.relative_to(root)
                dest.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(file_path, dest)
                written_files.append(str(dest))
                logger.info("Copied %s", file_path.name)
        return temp_dir, written_files
