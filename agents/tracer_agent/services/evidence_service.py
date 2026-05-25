import logging
import os
from pathlib import Path

from services.ast_service import AstService

logger = logging.getLogger(__name__)


class EvidenceService:
    def __init__(self, ast_service: AstService):
        self._ast = ast_service

    def build(self, file_paths: list[str], call_graph: dict) -> dict:
        if not file_paths:
            return {"signatures": {}, "import_edges": [], "call_edges": [], "confirmed_edges": []}
        base = self._compute_base(file_paths)
        files = self._read_files(file_paths, base)
        signatures = self._build_signatures(files)
        import_graph = self._ast.build_import_graph(files)
        import_edges = [
            {"from": cls, "to": imp}
            for cls, imports in import_graph.items()
            for imp in imports
        ]
        call_edges = call_graph.get("edges", [])
        confirmed_edges = self._intersect(import_edges, call_edges)
        return {
            "signatures": signatures,
            "import_edges": import_edges,
            "call_edges": call_edges,
            "confirmed_edges": confirmed_edges,
        }

    def _compute_base(self, file_paths: list[str]) -> Path:
        try:
            base = Path(os.path.commonpath(file_paths))
        except ValueError:
            return Path(file_paths[0]).parent
        return base.parent if base.suffix == ".py" else base

    def _read_files(self, file_paths: list[str], base: Path) -> dict[str, str]:
        files: dict[str, str] = {}
        for fp in file_paths:
            try:
                content = Path(fp).read_text(encoding="utf-8")
                try:
                    rel = str(Path(fp).relative_to(base))
                except ValueError:
                    rel = Path(fp).name
                files[rel] = content
            except OSError:
                logger.warning("Could not read %s", fp)
        return files

    def _build_signatures(self, files: dict[str, str]) -> dict:
        signatures: dict = {}
        for rel, content in files.items():
            sigs = self._ast.extract_signatures(rel, content)
            signatures.update(sigs)
        return signatures

    def _intersect(self, import_edges: list[dict], call_edges: list[dict]) -> list[dict]:
        call_set = {(e["from"], e["to"]) for e in call_edges}
        return [e for e in import_edges if (e["from"], e["to"]) in call_set]
