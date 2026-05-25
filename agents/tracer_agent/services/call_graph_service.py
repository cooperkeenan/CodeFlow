import json
import logging
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
        resolved_files = self._resolve_entry_files(entry_files)
        logger.info("Entry files: %d", len(resolved_files))
        try:
            binary = self._find_binary()
            result = subprocess.run(
                [binary] + resolved_files + ["--package", temp_dir, "--precision", "-o", str(output_path)],
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
            shutil.rmtree(str(output_path.parent), ignore_errors=True)
            logger.info("Cleaned up jarviscg output dir")

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

    def _resolve_entry_files(self, entry_files: list[str]) -> list[str]:
        return entry_files

    def _class_name_from_node(self, node: str) -> str | None:
        for part in reversed(node.split(".")):
            if part and part[0].isupper():
                return part
        return None

    def _to_serialisable(self, raw: dict[str, list[str]]) -> dict:
        class_edges: set[tuple[str, str]] = set()
        for caller, callees in raw.items():
            src = self._class_name_from_node(caller)
            if not src:
                continue
            for callee in callees:
                tgt = self._class_name_from_node(callee)
                if not tgt or src == tgt:
                    continue
                class_edges.add((src, tgt))
        edges = [{"from": s, "to": t} for s, t in class_edges]
        nodes = list({n for e in edges for n in (e["from"], e["to"])})
        return {"nodes": nodes, "edges": edges}
