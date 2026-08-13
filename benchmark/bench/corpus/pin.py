import subprocess
from datetime import datetime, timezone

from bench.config.corpus_model import CorpusRepo, Pin


class RefResolutionError(RuntimeError):
    """A corpus ref could not be resolved to a commit."""


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


class CommitPinner:
    """Resolves a corpus repo's branch/tag ref to an immutable commit SHA."""

    def __init__(self, timeout_seconds: int = 120) -> None:
        self._timeout = timeout_seconds

    def resolve(self, repo: CorpusRepo, resolved_at: str) -> Pin:
        sha = self._resolve_sha(repo.url, repo.ref)
        return Pin(name=repo.name, url=repo.url, sha=sha, resolved_at=resolved_at)

    def _resolve_sha(self, url: str, ref: str) -> str:
        try:
            result = subprocess.run(
                ["git", "ls-remote", url, ref],
                capture_output=True,
                text=True,
                timeout=self._timeout,
            )
        except subprocess.TimeoutExpired as exc:
            raise RefResolutionError(f"git ls-remote timed out for {url} ({ref})") from exc

        if result.returncode != 0:
            raise RefResolutionError(
                f"git ls-remote failed for {url} ({ref}): {result.stderr.strip() or 'no stderr'}"
            )
        return self._pick(result.stdout, url, ref)

    def _pick(self, stdout: str, url: str, ref: str) -> str:
        candidates: dict[str, str] = {}
        for line in stdout.splitlines():
            parts = line.split()
            if len(parts) == 2:
                candidates[parts[1]] = parts[0]

        if not candidates:
            raise RefResolutionError(f"ref {ref!r} not found on {url}")

        for name in (f"refs/heads/{ref}", f"refs/tags/{ref}^{{}}", f"refs/tags/{ref}", ref):
            if name in candidates:
                return candidates[name]
        return candidates[sorted(candidates)[0]]
