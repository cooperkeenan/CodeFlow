import logging
from pathlib import Path

from services.evidence.ast_service import AstService

logger = logging.getLogger(__name__)


class EvidenceService:
    def __init__(self, ast_service: AstService):
        self._ast = ast_service

    def build(self, file_paths: list[str], call_graph: dict, temp_dir: str) -> dict:
        if not file_paths:
            return {"signatures": {}, "import_edges": [], "call_edges": [], "confirmed_edges": [], "http_edges": []}
        files = self._read_files(file_paths, Path(temp_dir))
        signatures = self._build_signatures(files)
        import_graph = self._ast.build_import_graph(files)
        import_edges = [
            {"from": cls, "to": imp}
            for cls, imports in import_graph.items()
            for imp in imports
        ]
        call_edges = call_graph.get("edges", [])
        confirmed_edges = self._intersect(import_edges, call_edges)
        http_edges = self._build_http_edges(files)
        return {
            "signatures": signatures,
            "import_edges": import_edges,
            "call_edges": call_edges,
            "confirmed_edges": confirmed_edges,
            "http_edges": http_edges,
        }

    def _read_files(self, file_paths: list[str], base: Path) -> dict[str, str]:
        files: dict[str, str] = {}
        for fp in file_paths:
            try:
                content = Path(fp).read_text(encoding="utf-8")
                try:
                    rel = Path(fp).relative_to(base).as_posix()
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

    def _build_http_edges(self, files: dict[str, str]) -> list[dict]:
        edges: list[dict] = []
        for rel, content in files.items():
            edges.extend(self._ast.extract_http_calls(rel, content))
        return edges

    def _intersect(self, import_edges: list[dict], call_edges: list[dict]) -> list[dict]:
        call_set = {(e["from"], e["to"]) for e in call_edges}
        return [e for e in import_edges if (e["from"], e["to"]) in call_set]
