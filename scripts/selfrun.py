import ast
import os
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "agents" / "render_agent"))
sys.path.insert(0, str(ROOT / "agents" / "tracer_agent"))

from services.analysis.budget_config import BudgetConfig
from services.analysis.flow_pipeline import FlowPipeline
from services.analysis.effect_detector_factory import build_effect_detector
from services.analysis.flow_stitcher_factory import build_flow_stitcher
from services.analysis.heuristic_decision_judge import HeuristicDecisionJudge
from services.analysis.page_budgeter_factory import build_page_budgeter
from services.analysis.project_indexer_factory import build_project_indexer
from services.analysis.site_classifier import SiteClassifier
from placement.flow_page_placer_factory import build_flow_page_placer

_GUARD_SELECTOR = re.compile(r"\bnot\b|is None|!=\s*None")


def read_sources() -> dict[str, str]:
    files: dict[str, str] = {}
    for base in ("agents", "shared", "api"):
        for path in (ROOT / base).glob("**/*.py"):
            try:
                text = path.read_text(encoding="utf-8")
                ast.parse(text)
                files[path.relative_to(ROOT).as_posix()] = text
            except (OSError, SyntaxError):
                continue
    return files


def build_pipeline() -> FlowPipeline:
    return FlowPipeline(
        build_project_indexer(),
        build_effect_detector(),
        build_flow_stitcher(),
        build_page_budgeter(),
        judge=HeuristicDecisionJudge(SiteClassifier()),
    )


def check(label: str, ok: bool, detail: str = "") -> bool:
    print(f"  [{'PASS' if ok else 'FAIL'}] {label}{': ' + detail if detail else ''}")
    return ok


def main() -> int:
    files = read_sources()
    pipeline = build_pipeline()
    graph = pipeline.run("CodeFlow", files)
    canonical_first = _canonical(pipeline.run("CodeFlow", files))
    canonical_second = _canonical(pipeline.run("CodeFlow", files))
    view = build_flow_page_placer().place(graph)

    lanes = {lane.id.replace("agents.", "").replace("_agent", "") for lane in graph.lanes}
    stitches = [e for e in graph.edges if e.kind == "stitch"]
    decisions = [n for n in graph.nodes if n.kind == "decision"]
    guard_decisions = [n for n in decisions if _GUARD_SELECTOR.search(n.label)]
    no_refs = [n.id for n in graph.nodes if not n.refs]

    print(f"lanes={sorted(lanes)} nodes={len(graph.nodes)} edges={len(graph.edges)} "
          f"stitches={len(stitches)} decisions={len(decisions)} rendered={len(view.nodes)}")
    budget = BudgetConfig().node_budget
    print("Assertions:")
    results = [
        check("lanes == {api, profiler, tracer, layout, render}",
              lanes == {"api", "profiler", "tracer", "layout", "render"}, str(sorted(lanes))),
        check(">=4 stitch edges api->agent entries", len(stitches) >= 4, f"{len(stitches)} stitches"),
        check("two runs byte-identical (ignoring llm_*)",
              canonical_first == canonical_second),
        check("node count within budget ceiling",
              len(graph.nodes) <= budget + len(graph.lanes) * 3, f"{len(graph.nodes)} nodes"),
        check("no guard-selector decision survives",
              len(guard_decisions) == 0, f"{len(guard_decisions)} guard decisions"),
    ]
    print(f"provenance: {len(graph.nodes) - len(no_refs)}/{len(graph.nodes)} nodes carry a SourceRef "
          f"(entries lack refs by construction: {len(no_refs)} without)")
    print(f"decisions: {len(decisions)} survive the budget on this repo "
          f"(CodeFlow is a near-linear service pipeline; node_budget={budget})")
    return 0 if all(results) else 1


def _canonical(graph) -> str:
    stripped = graph.model_copy(deep=True)
    stripped.page_title = ""
    for node in stripped.nodes:
        node.llm_label = None
    for edge in stripped.edges:
        edge.llm_label = None
    for lane in stripped.lanes:
        lane.llm_title = None
    return stripped.model_dump_json()


if __name__ == "__main__":
    os.environ.setdefault("ANTHROPIC_API_KEY", "x")
    raise SystemExit(main())
