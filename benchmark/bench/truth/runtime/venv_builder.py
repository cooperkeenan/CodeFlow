import subprocess
import sys
import tomllib
from dataclasses import dataclass
from pathlib import Path


class VenvBuildError(RuntimeError):
    """A probe virtualenv could not be created."""


@dataclass(frozen=True)
class VenvResult:
    """A probe environment plus an honest record of how well it was populated.

    `install_error` is surfaced rather than swallowed: a probe that fails because
    its dependencies did not install is a different fact from a probe that fails
    because the application cannot boot, and the results must be able to tell
    those apart.
    """

    python: Path
    dependencies: tuple[str, ...]
    install_error: str | None


class ProbeVenvBuilder:
    """Builds a per-repo virtualenv so a probe can import the repo for real."""

    def __init__(self, venvs_dir: Path, timeout_seconds: int = 1800) -> None:
        # Absolute: probes run with cwd set to the target repo, so a relative path
        # here would resolve against the wrong root.
        self._venvs_dir = venvs_dir.resolve()
        self._timeout = timeout_seconds

    def python_for(self, slug: str) -> Path:
        return self._venvs_dir / slug / "bin" / "python"

    def is_ready(self, slug: str) -> bool:
        return (self._venvs_dir / slug / ".deps-installed").exists()

    def discover_dependencies(self, project_dir: Path) -> list[str]:
        pyproject = project_dir / "pyproject.toml"
        if pyproject.exists():
            try:
                data = tomllib.loads(pyproject.read_text(encoding="utf-8"))
            except (tomllib.TOMLDecodeError, OSError):
                data = {}
            deps = data.get("project", {}).get("dependencies") or []
            if deps:
                return [str(dep) for dep in deps]

        for candidate in ("requirements.txt", "requirements/base.txt", "requirements/prod.txt"):
            path = project_dir / candidate
            if path.exists():
                return [
                    line.strip()
                    for line in path.read_text(encoding="utf-8").splitlines()
                    if line.strip() and not line.strip().startswith(("#", "-"))
                ]
        return []

    def ensure(self, slug: str, project_dir: Path) -> VenvResult:
        venv_dir = self._venvs_dir / slug
        marker = venv_dir / ".deps-installed"
        dependencies = tuple(self.discover_dependencies(project_dir))

        if self.is_ready(slug):
            recorded = (venv_dir / ".install-error")
            return VenvResult(
                python=self.python_for(slug),
                dependencies=dependencies,
                install_error=recorded.read_text() if recorded.exists() else None,
            )

        venv_dir.parent.mkdir(parents=True, exist_ok=True)
        result = self._run([sys.executable, "-m", "venv", str(venv_dir)])
        if result.returncode != 0:
            raise VenvBuildError(f"could not create venv for {slug}: {result.stderr.strip()}")

        install_error: str | None = None
        if dependencies:
            pip = venv_dir / "bin" / "pip"
            install = self._run(
                [str(pip), "install", "-q", "--disable-pip-version-check", *dependencies]
            )
            if install.returncode != 0:
                install_error = (install.stderr.strip() or "pip failed")[-1200:]
                (venv_dir / ".install-error").write_text(install_error)

        marker.write_text("\n".join(sorted(dependencies)) + "\n")
        return VenvResult(
            python=self.python_for(slug),
            dependencies=dependencies,
            install_error=install_error,
        )

    def _run(self, argv: list[str]) -> subprocess.CompletedProcess[str]:
        try:
            return subprocess.run(argv, capture_output=True, text=True, timeout=self._timeout)
        except subprocess.TimeoutExpired as exc:
            raise VenvBuildError(f"timed out: {' '.join(argv[:3])}") from exc
