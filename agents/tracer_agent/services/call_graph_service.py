import json
import logging
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

logger = logging.getLogger(__name__)


class CallGraphService:
    def build(
        self,
        temp_dir: str,
        entry_files: list[str],
        entry_point_hint: str | None = None,
    ) -> dict:
        logger.info("Running jarviscg on %d files in %s", len(entry_files), temp_dir)
        output_path = Path(tempfile.mkdtemp()) / "callgraph.json"
        entry_file = self._resolve_entry_file(entry_files, entry_point_hint)
        logger.info("Entry file: %s", entry_file)
        try:
            binary = self._find_binary()
            result = subprocess.run(
                [binary, entry_file, "--package", temp_dir, "--precision", "-o", str(output_path)],
                capture_output=True,
                text=True,
                timeout=120,
            )
            if result.returncode != 0:
                raise RuntimeError(f"jarviscg exited {result.returncode}: {result.stderr}")

            with open(output_path) as f:
                raw: dict[str, list[str]] = json.load(f)

            graph = self._to_serialisable(raw)
            logger.info(
                "Call graph built: %d nodes, %d edges",
                len(graph["nodes"]),
                len(graph["edges"]),
            )
            return graph
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)
            shutil.rmtree(str(output_path.parent), ignore_errors=True)
            logger.info("Cleaned up temp dirs")

    def _find_binary(self) -> str:
        on_path = shutil.which("jarviscg")
        if on_path:
            return on_path
        venv_bin = Path(sys.executable).parent / "jarviscg"
        if venv_bin.exists():
            return str(venv_bin)
        raise RuntimeError(
            f"jarviscg not found. Install with: pip install git+https://github.com/nuanced-dev/jarviscg\n"
            f"sys.executable={sys.executable}"
        )

    def _resolve_entry_file(self, entry_files: list[str], hint: str | None) -> str:
        if hint:
            for match in re.findall(r"[\w./\-]+\.py", hint):
                stem = Path(match).name
                for f in entry_files:
                    if Path(f).name == stem:
                        return f
        for preferred in ("app.py", "main.py"):
            for f in entry_files:
                if Path(f).name == preferred:
                    return f
        return entry_files[0]

    def _to_serialisable(self, raw: dict[str, list[str]]) -> dict:
        edges = [
            {"from": caller, "to": callee}
            for caller, callees in raw.items()
            for callee in callees
            if caller != callee
        ][:300]
        nodes = list({n for e in edges for n in (e["from"], e["to"])})
        return {"nodes": nodes, "edges": edges}