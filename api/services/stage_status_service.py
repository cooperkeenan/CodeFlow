import json
from datetime import datetime, timezone
from pathlib import Path

_PROJECT_ROOT = Path(__file__).resolve().parents[2]
_RUNS_PATH = _PROJECT_ROOT / "shared" / "outputs" / "stage_runs.json"

STAGE_ORDER = ["profiler", "tracer", "render"]

_STAGE_DIRS: dict[str, Path] = {
    "profiler": _PROJECT_ROOT / "agents" / "profiler_agent",
    "tracer":   _PROJECT_ROOT / "agents" / "tracer_agent",
    "render":   _PROJECT_ROOT / "agents" / "render_agent",
}


class StageStatusService:
    def record_run(self, stage: str) -> None:
        runs = self._load_runs()
        idx = STAGE_ORDER.index(stage)
        now = datetime.now(timezone.utc).isoformat()
        for s in STAGE_ORDER[idx:]:
            runs[s] = now
        _RUNS_PATH.write_text(json.dumps(runs, indent=2))

    def get_recommendation(self) -> dict:
        runs = self._load_runs()
        dirty: list[str] = []
        for stage in STAGE_ORDER:
            last_run_str = runs.get(stage)
            if last_run_str is None:
                dirty.append(stage)
                continue
            last_run_ts = datetime.fromisoformat(last_run_str).timestamp()
            agent_dir = _STAGE_DIRS[stage]
            if not agent_dir.exists():
                continue
            max_mtime = max((f.stat().st_mtime for f in agent_dir.rglob("*.py")), default=0.0)
            if max_mtime > last_run_ts:
                dirty.append(stage)
        return {"recommended_stage": dirty[0] if dirty else None, "dirty_stages": dirty}

    def _load_runs(self) -> dict:
        if not _RUNS_PATH.exists():
            return {}
        try:
            return json.loads(_RUNS_PATH.read_text())
        except Exception:
            return {}
