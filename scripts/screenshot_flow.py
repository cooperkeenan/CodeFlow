import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))
sys.path.insert(0, str(REPO_ROOT / "agents" / "render_agent"))
sys.path.insert(0, str(REPO_ROOT / "agents" / "tracer_agent"))

from render_repo import load_dotenv, read_python_sources
from save_command import parse_save_flag, save_to_account
from services.analysis.flow_pipeline import FlowPipeline
from services.analysis.decision_judge_factory import build_decision_judge
from services.analysis.flow_namer_factory import build_flow_namer
from services.analysis.flow_reviewer_factory import build_flow_reviewer
from services.analysis.heuristic_decision_judge import HeuristicDecisionJudge
from services.analysis.heuristic_flow_namer import HeuristicFlowNamer
from services.analysis.heuristic_flow_reviewer import HeuristicFlowReviewer
from services.analysis.site_classifier import SiteClassifier
from services.analysis.effect_detector_factory import build_effect_detector
from services.analysis.flow_stitcher_factory import build_flow_stitcher
from services.analysis.visibility_budgeter_factory import build_visibility_budgeter
from services.analysis.project_indexer_factory import build_project_indexer
from placement.flow_page_placer_factory import build_flow_page_placer

from chrome_locator import ChromeLocator
from dev_server_screenshotter import DevServerScreenshotter

FIXTURE_PATH = REPO_ROOT / "frontend" / "public" / "fixture" / "rendered_view.json"
FLOW_URL = "http://localhost:5173/flow-fixture"
DEV_PORT = 5173
_CACHE_PATH = REPO_ROOT / ".cache" / "decision_verdicts.json"
_NAME_CACHE_PATH = REPO_ROOT / ".cache" / "node_names.json"
_REVIEW_CACHE_PATH = REPO_ROOT / ".cache" / "review_findings.json"


def _build_view(target: Path, no_llm: bool):
    files = read_python_sources(target)
    print(f"Indexed {len(files)} Python files from {target}")
    judge = HeuristicDecisionJudge(SiteClassifier()) if no_llm else build_decision_judge(_CACHE_PATH)
    namer = HeuristicFlowNamer() if no_llm else build_flow_namer(_NAME_CACHE_PATH)
    reviewer = HeuristicFlowReviewer() if no_llm else build_flow_reviewer(_REVIEW_CACHE_PATH)
    pipeline = FlowPipeline(
        build_project_indexer(), build_effect_detector(),
        build_flow_stitcher(), build_visibility_budgeter(),
        judge=judge, namer=namer, reviewer=reviewer,
        embed_symbol_sources=True,
    )
    graph = pipeline.run(target.name, files)
    view = build_flow_page_placer().place(graph)
    return graph, view


def _write_outputs(graph, view, out_dir: Path) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    graph_json = graph.model_dump_json(indent=2)
    view_json = json.dumps(view.model_dump(), indent=2)
    (out_dir / "flow_graph.json").write_text(graph_json)
    (out_dir / "rendered_view.json").write_text(view_json)
    FIXTURE_PATH.parent.mkdir(parents=True, exist_ok=True)
    FIXTURE_PATH.write_text(view_json)


def _print_summary(graph, png_path: Path) -> None:
    kinds: dict[str, int] = {}
    for node in graph.nodes:
        kinds[node.kind] = kinds.get(node.kind, 0) + 1
    decisions = [n for n in graph.nodes if n.kind == "decision"]
    print(f"lanes={len(graph.lanes)} nodes={len(graph.nodes)} kinds={kinds}")
    print(f"decisions ({len(decisions)}):")
    for node in decisions:
        print(f"  - {node.label}")
    if not png_path.exists():
        print(f"ERROR: screenshot was not produced at {png_path}")
        raise SystemExit(1)
    size = png_path.stat().st_size
    print(f"wrote {png_path} ({size} bytes)")


def main(argv: list[str]) -> int:
    load_dotenv(REPO_ROOT / ".env")
    save_handle, rest = parse_save_flag(argv[1:])
    no_llm = "--no-llm" in rest
    expand = ""
    if "--expand" in rest:
        index = rest.index("--expand")
        expand = rest[index + 1] if index + 1 < len(rest) else ""
        rest = rest[:index] + rest[index + 2 :]
    positional = [a for a in rest if a != "--no-llm"]
    if len(positional) < 1:
        print("usage: screenshot_flow.py <repo_path> [out_dir] [--no-llm] [--save <handle>]")
        return 1
    target = Path(positional[0]).resolve()
    out_dir = Path(positional[1]).resolve() if len(positional) > 1 else REPO_ROOT / "scratch_out"

    graph, view = _build_view(target, no_llm)
    _write_outputs(graph, view, out_dir)

    png_path = out_dir / "flow.png"
    screenshotter = DevServerScreenshotter(
        frontend_dir=REPO_ROOT / "frontend",
        port=DEV_PORT,
        chrome_path=ChromeLocator().find(),
        url=f"{FLOW_URL}?expand={expand}" if expand else FLOW_URL,
        out_png=png_path,
    )
    screenshotter.run()

    _print_summary(graph, png_path)
    if save_handle is not None:
        return save_to_account(target.name, graph, view, save_handle)
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
