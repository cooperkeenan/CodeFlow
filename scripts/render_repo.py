import json
import os
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))
sys.path.insert(0, str(REPO_ROOT / "agents" / "render_agent"))
sys.path.insert(0, str(REPO_ROOT / "agents" / "tracer_agent"))

from tracer.services.analysis.flow_pipeline import FlowPipeline
from tracer.services.analysis.significance.factory import build_decision_judge
from tracer.services.analysis.labelling.factory import build_flow_namer
from tracer.services.analysis.labelling.factory import build_flow_reviewer
from tracer.services.analysis.significance.heuristic_decision_judge import HeuristicDecisionJudge
from tracer.services.analysis.labelling.heuristics import HeuristicFlowNamer
from tracer.services.analysis.labelling.heuristics import HeuristicFlowReviewer
from tracer.services.analysis.significance.site_classifier import SiteClassifier
from tracer.services.analysis.effects.factory import build_effect_detector
from tracer.services.analysis.stitch.factory import build_flow_stitcher
from tracer.services.analysis.budget.factory import build_visibility_budgeter
from tracer.services.analysis.indexing.factory import build_project_indexer
from render.placement.flow_page_placer_factory import build_flow_page_placer

from repo_map_saving.save_command import parse_save_flag, save_to_account

_SKIP_DIRS = {".git", "node_modules", ".venv", "venv", "__pycache__", "dist", "build"}
_CACHE_PATH = REPO_ROOT / ".cache" / "decision_verdicts.json"
_NAME_CACHE_PATH = REPO_ROOT / ".cache" / "node_names.json"
_REVIEW_CACHE_PATH = REPO_ROOT / ".cache" / "review_findings.json"


def load_dotenv(path: Path) -> None:
    if not path.exists():
        return
    for line in path.read_text().splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or "=" not in stripped:
            continue
        key, _, value = stripped.partition("=")
        os.environ.setdefault(key.strip(), value.strip())


def _is_test_path(relpath: Path) -> bool:
    if any(part in ("tests", "test") for part in relpath.parts):
        return True
    name = relpath.name
    return name.startswith("test_") or name.endswith("_test.py") or name == "conftest.py"


def read_python_sources(target: Path, include_tests: bool = False) -> dict[str, str]:
    files: dict[str, str] = {}
    for path in target.rglob("*.py"):
        if any(part in _SKIP_DIRS for part in path.parts):
            continue
        relpath = path.relative_to(target)
        if not include_tests and _is_test_path(relpath):
            continue
        try:
            files[relpath.as_posix()] = path.read_text(encoding="utf-8")
        except OSError:
            continue
    return files


def _print_significance(pipeline: FlowPipeline) -> None:
    significance = pipeline.last_significance()
    if significance is None:
        return
    print(f"significance-stage decisions ({len(significance.ranked_decisions)}):")
    for site_id in significance.ranked_decisions:
        verdict = significance.verdicts[site_id]
        print(f"  - [{site_id}] {verdict.question or '(no question)'}")


def _print_review(pipeline: FlowPipeline) -> None:
    findings = pipeline.last_review()
    if findings is None:
        return
    print(f"review findings ({len(findings)}):")
    for finding in findings:
        print(f"  - [{finding.node_id}] {finding.issue}")


def main(argv: list[str]) -> int:
    load_dotenv(REPO_ROOT / ".env")
    save_handle, rest = parse_save_flag(argv[1:])
    include_tests = "--include-tests" in rest
    no_llm = "--no-llm" in rest
    positional = [a for a in rest if a not in ("--include-tests", "--no-llm")]
    target = Path(positional[0]).resolve() if len(positional) > 0 else REPO_ROOT
    out_dir = Path(positional[1]).resolve() if len(positional) > 1 else REPO_ROOT / "scratch_out"
    out_dir.mkdir(parents=True, exist_ok=True)

    files = read_python_sources(target, include_tests)
    print(f"Indexed {len(files)} Python files from {target}")
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    judge = HeuristicDecisionJudge(SiteClassifier()) if no_llm else build_decision_judge(api_key, _CACHE_PATH)
    namer = HeuristicFlowNamer() if no_llm else build_flow_namer(api_key, _NAME_CACHE_PATH)
    reviewer = HeuristicFlowReviewer() if no_llm else build_flow_reviewer(api_key, _REVIEW_CACHE_PATH)
    pipeline = FlowPipeline(
        build_project_indexer(), build_effect_detector(),
        build_flow_stitcher(api_key), build_visibility_budgeter(),
        judge=judge, namer=namer, reviewer=reviewer,
        embed_symbol_sources=True,
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
    _print_significance(pipeline)
    _print_review(pipeline)
    print(f"wrote {out_dir / 'flow_graph.json'}")
    print(f"wrote {out_dir / 'rendered_view.json'}")
    if save_handle is not None:
        return save_to_account(target.name, graph, view, save_handle)
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
