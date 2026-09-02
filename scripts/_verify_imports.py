import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
AGENTS = {
    "api": ROOT / "api",
    "explain": ROOT / "agents/explain_agent",
    "profiler": ROOT / "agents/profiler_agent",
    "render": ROOT / "agents/render_agent",
    "tracer": ROOT / "agents/tracer_agent",
}

_CODE = "import main; print('ok')"


def check(name: str, agent_dir: Path) -> bool:
    env = {"PYTHONPATH": f"{agent_dir}:{ROOT}", "ANTHROPIC_API_KEY": "dummy",
           "DATABASE_URL": "postgresql://x/y", "PATH": "/usr/bin:/bin",
           "GITHUB_CLIENT_ID": "x", "GITHUB_CLIENT_SECRET": "y"}
    proc = subprocess.run(
        [sys.executable, "-c", _CODE], cwd=str(agent_dir), env=env,
        capture_output=True, text=True,
    )
    if proc.returncode == 0:
        print(f"PASS {name}: import main OK")
        return True
    tail = proc.stderr.strip().splitlines()[-3:]
    print(f"FAIL {name}:")
    for line in tail:
        print("   ", line)
    return False


if __name__ == "__main__":
    targets = sys.argv[1:] or list(AGENTS)
    results = [check(t, AGENTS[t]) for t in targets]
    sys.exit(0 if all(results) else 1)
