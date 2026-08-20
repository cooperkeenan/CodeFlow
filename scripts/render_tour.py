import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))
sys.path.insert(0, str(REPO_ROOT / "agents" / "render_agent"))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from tour.tour_builders import REPO_URL
from tour.tour_graph_builder import build_beats, build_tour_graph
from tour.tour_placer import TourPlacer
from tour.tour_steps import build_steps
from tour.tour_validator import validate_tour

TOUR_PATH = REPO_ROOT / "frontend" / "public" / "tour" / "codeflow_tour.json"
OUT_DIR = REPO_ROOT / "scratch_out" / "tour"


def main() -> int:
    beats = build_beats()
    graph = build_tour_graph(beats)
    view = TourPlacer().place(graph, beats)
    steps = build_steps(beats)
    validate_tour(graph, beats, view)

    payload = {
        "page_title": graph.page_title,
        "repo": graph.repo,
        "repo_url": REPO_URL,
        "view": view.model_dump(),
        "steps": steps,
    }
    TOUR_PATH.parent.mkdir(parents=True, exist_ok=True)
    TOUR_PATH.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    (OUT_DIR / "flow_graph.json").write_text(graph.model_dump_json(indent=2), encoding="utf-8")
    (OUT_DIR / "rendered_view.json").write_text(
        json.dumps(view.model_dump(), indent=2, sort_keys=True), encoding="utf-8"
    )

    decisions = [beat for beat in beats if beat.kind == "decision"]
    arms = sum(len(beat.arms) for beat in beats)
    converging = sum(len(beat.converging()) for beat in beats)
    height = max(item["position"]["y"] for item in view.nodes)
    print(f"main line   {len(beats)} beats  ({len(decisions)} decisions)")
    print(f"branches    {arms} arms  ({converging} converge, {arms - converging} stop)")
    print(f"graph       {len(graph.nodes)} nodes / {len(graph.edges)} edges")
    print(f"canvas      {len(view.nodes)} drawn, {height + 200}px tall")
    print(f"wrote {TOUR_PATH}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
