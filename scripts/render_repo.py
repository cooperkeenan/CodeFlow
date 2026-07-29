import ast
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))
sys.path.insert(0, str(REPO_ROOT / "agents" / "render_agent"))
sys.path.insert(0, str(REPO_ROOT / "agents" / "tracer_agent"))

from services.analysis.flow_pipeline import FlowPipeline
from services.analysis.effect_detector_factory import build_effect_detector
from services.analysis.flow_stitcher_factory import build_flow_stitcher
from services.analysis.page_budgeter_factory import build_page_budgeter
from services.analysis.project_indexer_factory import build_project_indexer
from placement.flow_page_placer_factory import build_flow_page_placer

_SKIP_DIRS = {".git", "node_modules", ".venv", "venv", "__pycache__", "dist", "build"}


def read_python_sources(target: Path) -> dict[str, str]:
    files: dict[str, str] = {}
    for path in target.rglob("*.py"):
        if any(part in _SKIP_DIRS for part in path.parts):
            continue
        try:
            text = path.read_text(encoding="utf-8")
            ast.parse(text)
            files[path.relative_to(target).as_posix()] = text
        except (OSError, SyntaxError):
            continue
    return files


def main(argv: list[str]) -> int:
    target = Path(argv[1]).resolve() if len(argv) > 1 else REPO_ROOT
    out_dir = Path(argv[2]).resolve() if len(argv) > 2 else REPO_ROOT / "scratch_out"
    out_dir.mkdir(parents=True, exist_ok=True)

    files = read_python_sources(target)
    print(f"Indexed {len(files)} Python files from {target}")
    pipeline = FlowPipeline(
        build_project_indexer(), build_effect_detector(),
        build_flow_stitcher(), build_page_budgeter(),
    )
    graph = pipeline.run(target.name, files)
    view = build_flow_page_placer().place(graph)

    (out_dir / "flow_graph.json").write_text(graph.model_dump_json(indent=2))
    (out_dir / "rendered_view.json").write_text(json.dumps(view.model_dump(), indent=2))

    kinds: dict[str, int] = {}
    for node in graph.nodes:
        kinds[node.kind] = kinds.get(node.kind, 0) + 1
    decisions = [n for n in graph.nodes if n.kind == "decision"]
    print(f"lanes={len(graph.lanes)} nodes={len(graph.nodes)} kinds={kinds}")
    print(f"decisions ({len(decisions)}):")
    for node in decisions:
        print(f"  - {node.label}")
    print(f"wrote {out_dir / 'flow_graph.json'}")
    print(f"wrote {out_dir / 'rendered_view.json'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
