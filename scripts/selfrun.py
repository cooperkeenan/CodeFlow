import os
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "agents" / "render_agent"))
sys.path.insert(0, str(ROOT / "agents" / "tracer_agent"))

from services.analysis.budget_config import BudgetConfig
from services.analysis.decision_judge import DecisionJudge
from services.analysis.decision_judge_factory import build_decision_judge
from services.analysis.flow_naming import FlowNaming
from services.analysis.flow_namer_factory import build_flow_namer
from services.analysis.flow_pipeline import FlowPipeline
from services.analysis.flow_reviewer_factory import build_flow_reviewer
from services.analysis.flow_reviewing import FlowReviewing
from services.analysis.effect_detector_factory import build_effect_detector
from services.analysis.flow_stitcher_factory import build_flow_stitcher
from services.analysis.heuristic_decision_judge import HeuristicDecisionJudge
from services.analysis.visibility_budgeter_factory import build_visibility_budgeter
from services.analysis.project_indexer_factory import build_project_indexer
from placement.flow_page_placer_factory import build_flow_page_placer
from render_repo import load_dotenv, read_python_sources

_GUARD_SELECTOR = re.compile(r"\bnot\b|is None|!=\s*None")
_CACHE_PATH = ROOT / ".cache" / "decision_verdicts.json"
_NAME_CACHE_PATH = ROOT / ".cache" / "node_names.json"
_REVIEW_CACHE_PATH = ROOT / ".cache" / "review_findings.json"


def read_sources() -> dict[str, str]:
    return read_python_sources(ROOT)


def build_pipeline(
    judge: DecisionJudge, namer: FlowNaming, reviewer: FlowReviewing, api_key: str | None
) -> FlowPipeline:
    return FlowPipeline(
        build_project_indexer(),
        build_effect_detector(),
        build_flow_stitcher(api_key),
        build_visibility_budgeter(),
        judge=judge,
        namer=namer,
        reviewer=reviewer,
        embed_symbol_sources=True,
    )


def check(label: str, ok: bool, detail: str = "") -> bool:
    print(f"  [{'PASS' if ok else 'FAIL'}] {label}{': ' + detail if detail else ''}")
    return ok


def main() -> int:
    load_dotenv(ROOT / ".env")
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    judge = build_decision_judge(api_key, _CACHE_PATH)
    namer = build_flow_namer(api_key, _NAME_CACHE_PATH)
    reviewer = build_flow_reviewer(api_key, _REVIEW_CACHE_PATH)
    used_llm = not isinstance(judge, HeuristicDecisionJudge)

    files = read_sources()
    pipeline = build_pipeline(judge, namer, reviewer, api_key)
    graph = pipeline.run("CodeFlow", files)
    pre_review = pipeline.last_pre_review()
    canonical_first = _canonical(pipeline.run("CodeFlow", files))
    canonical_second = _canonical(pipeline.run("CodeFlow", files))
    view = build_flow_page_placer().place(graph)

    lanes = {lane.id.replace("agents.", "").replace("_agent", "") for lane in graph.lanes}
    stitches = [e for e in graph.edges if e.kind == "stitch"]
    decisions = [n for n in graph.nodes if n.kind == "decision"]
    guard_decisions = [n for n in decisions if _GUARD_SELECTOR.search(n.label)]
    no_refs = [n.id for n in graph.nodes if not n.refs]
    skeleton = [n for n in graph.nodes if n.level == 0]
    revealed = {n.id for n in graph.nodes if n.level == 1}
    parented: set[str] = set()
    for node in graph.nodes:
        parented.update(node.hidden_children)
    stranded = sorted(revealed - parented)

    print(f"judge={'LLM' if used_llm else 'heuristic (no ANTHROPIC_API_KEY)'}")
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
        check("skeleton node count within budget ceiling",
              len(skeleton) <= budget + len(graph.lanes) * 3,
              f"{len(skeleton)} skeleton nodes of {len(graph.nodes)} total"),
        check("every revealed node is reachable from a parent's hidden_children",
              not stranded, f"{len(stranded)} stranded"),
        check("node/edge counts unchanged across reviewer stage",
              pre_review is not None
              and len(pre_review.nodes) == len(graph.nodes)
              and len(pre_review.edges) == len(graph.edges),
              f"pre={len(pre_review.nodes) if pre_review else '?'}n/"
              f"{len(pre_review.edges) if pre_review else '?'}e "
              f"post={len(graph.nodes)}n/{len(graph.edges)}e"),
    ]
    if used_llm:
        results.append(
            check("no guard-selector decision survives",
                  len(guard_decisions) == 0, f"{len(guard_decisions)} guard decisions"))
    else:
        print("  [SKIP] no guard-selector decision survives: heuristic judge cannot "
              "distinguish a guard from a decision; requires the LLM judge (set "
              "ANTHROPIC_API_KEY)")
    print(f"provenance: {len(graph.nodes) - len(no_refs)}/{len(graph.nodes)} nodes carry a SourceRef "
          f"(entries lack refs by construction: {len(no_refs)} without)")
    print(f"decisions: {len(decisions)} emitted, all revealable; "
          f"{len(skeleton)} skeleton nodes form the collapsed page (node_budget={budget})")
    return 0 if all(results) else 1


def _canonical(graph) -> str:
    stripped = graph.model_copy(deep=True)
    stripped.page_title = ""
    stripped.meta.pop("review_findings", None)
    for node in stripped.nodes:
        node.llm_label = None
        node.one_liner = ""
    for edge in stripped.edges:
        edge.llm_label = None
    for lane in stripped.lanes:
        lane.llm_title = None
    return stripped.model_dump_json()


if __name__ == "__main__":
    raise SystemExit(main())
