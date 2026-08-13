import json
import os
import subprocess
import tempfile
from dataclasses import dataclass
from pathlib import Path

from bench.config.corpus_model import ProbeSpec
from bench.truth.runtime.venv_builder import ProbeVenvBuilder, VenvBuildError

PROBES_DIR = Path(__file__).resolve().parent / "probes"

PROBE_SCRIPTS = {
    "fastapi": "fastapi_probe.py",
    "flask": "flask_probe.py",
    "django": "django_probe.py",
    "console_scripts": "console_scripts_probe.py",
}


@dataclass(frozen=True)
class ProbeOutcome:
    ok: bool
    framework: str
    routes: tuple[dict, ...]
    error: str | None
    install_error: str | None

    @property
    def failure_reason(self) -> str | None:
        if self.ok:
            return None
        if self.install_error:
            return f"probe dependencies failed to install: {self.install_error.splitlines()[-1]}"
        return (self.error or "unknown probe failure").strip().splitlines()[-1]


class RuntimeProbe:
    """Boots a repo in its own venv and asks its framework what it registers."""

    def __init__(self, builder: ProbeVenvBuilder, timeout_seconds: int = 300) -> None:
        self._builder = builder
        self._timeout = timeout_seconds

    def supports(self, spec: ProbeSpec) -> bool:
        return spec.kind in PROBE_SCRIPTS

    def run(self, slug: str, repo_path: Path, spec: ProbeSpec) -> ProbeOutcome:
        script = PROBES_DIR / PROBE_SCRIPTS[spec.kind]
        if not script.exists():
            return ProbeOutcome(False, spec.kind, (), f"no probe implemented for {spec.kind}", None)

        source_root = (repo_path / (spec.source_root or "")).resolve()
        try:
            venv = self._builder.ensure(slug, source_root)
        except VenvBuildError as exc:
            return ProbeOutcome(False, spec.kind, (), str(exc), None)

        payload = self._invoke(venv.python, script, source_root, spec)
        return ProbeOutcome(
            ok=bool(payload.get("ok")),
            framework=spec.kind,
            routes=tuple(payload.get("routes", ())),
            error=payload.get("error"),
            install_error=venv.install_error,
        )

    def _invoke(self, python: Path, script: Path, source_root: Path, spec: ProbeSpec) -> dict:
        env = {k: v for k, v in os.environ.items() if not k.startswith("ANTHROPIC_")}
        env.update(spec.env_map)
        env["PYTHONDONTWRITEBYTECODE"] = "1"

        with tempfile.TemporaryDirectory() as work:
            output = Path(work) / "probe.json"
            argv = [
                str(python),
                str(script),
                str(source_root),
                spec.app_path or spec.settings_module or spec.distribution or "",
                str(output),
            ]
            try:
                subprocess.run(
                    argv,
                    cwd=source_root,
                    env=env,
                    capture_output=True,
                    text=True,
                    timeout=self._timeout,
                )
            except subprocess.TimeoutExpired:
                return {"ok": False, "error": f"probe timed out after {self._timeout}s"}

            if not output.exists():
                return {"ok": False, "error": "probe produced no result file"}
            try:
                return json.loads(output.read_text())
            except json.JSONDecodeError as exc:
                return {"ok": False, "error": f"probe emitted invalid JSON: {exc}"}
