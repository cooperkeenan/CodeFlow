import subprocess
from pathlib import Path

from bench.config.corpus_model import PinnedRepo


class CheckoutError(RuntimeError):
    """A pinned corpus repo could not be materialised on disk."""


class RepoCheckout:
    """Materialises a pinned repo at an exact commit under the corpus cache."""

    def __init__(self, cache_dir: Path, timeout_seconds: int = 900) -> None:
        self._cache_dir = cache_dir
        self._timeout = timeout_seconds

    def path_for(self, pinned: PinnedRepo) -> Path:
        return self._cache_dir / pinned.slug

    def is_ready(self, pinned: PinnedRepo) -> bool:
        path = self.path_for(pinned)
        if not (path / ".git").exists():
            return False
        return self._head(path) == pinned.pin.sha

    def ensure(self, pinned: PinnedRepo) -> Path:
        path = self.path_for(pinned)
        if self.is_ready(pinned):
            return path

        path.mkdir(parents=True, exist_ok=True)
        self._run(["git", "init", "-q"], path)
        self._run(["git", "remote", "remove", "origin"], path, check=False)
        self._run(["git", "remote", "add", "origin", pinned.pin.url], path)

        if not self._try_fetch_sha(path, pinned.pin.sha):
            self._run(["git", "fetch", "--depth", "1", "origin", pinned.repo.ref], path)
        self._run(["git", "checkout", "-q", "FETCH_HEAD"], path)

        head = self._head(path)
        if head != pinned.pin.sha:
            raise CheckoutError(
                f"{pinned.name}: checked out {head} but the lock pins {pinned.pin.sha}. "
                "Refusing to score against a corpus that does not match its lock."
            )
        return path

    def _try_fetch_sha(self, path: Path, sha: str) -> bool:
        result = self._run(
            ["git", "fetch", "--depth", "1", "origin", sha], path, check=False
        )
        return result.returncode == 0

    def _head(self, path: Path) -> str:
        result = self._run(["git", "rev-parse", "HEAD"], path, check=False)
        return result.stdout.strip() if result.returncode == 0 else ""

    def _run(
        self, argv: list[str], cwd: Path, check: bool = True
    ) -> subprocess.CompletedProcess[str]:
        try:
            result = subprocess.run(
                argv, cwd=cwd, capture_output=True, text=True, timeout=self._timeout
            )
        except subprocess.TimeoutExpired as exc:
            raise CheckoutError(f"timed out: {' '.join(argv)}") from exc
        if check and result.returncode != 0:
            raise CheckoutError(
                f"{' '.join(argv)} failed in {cwd}: {result.stderr.strip() or 'no stderr'}"
            )
        return result
