import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))
sys.path.insert(0, str(REPO_ROOT / "agents" / "render_agent"))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from tour.tour_beat import Beat
from tour.tour_builders import REPO_URL
from tour.tour_card_beats import splice_card_beats
from tour.tour_chapters import build_chapters, chapters_payload
from tour.tour_graph_builder import build_beat_groups, build_tour_graph
from tour.tour_placer import TourPlacer
from tour.tour_placer_factory import build_tour_placer
from tour.tour_shot_validator import validate_shots
from tour.tour_steps import build_steps
from tour.tour_validator import validate_tour

TOUR_PATH = REPO_ROOT / "frontend" / "public" / "tour" / "codeflow_tour.json"
OUT_DIR = REPO_ROOT / "scratch_out" / "tour"


def _print_grid_summary(placer: TourPlacer, beats: list[Beat]) -> None:
    for beat in beats:
        if len(beat.arms) < 6:
            continue
        cluster = placer.clusters[beat.id]
        arm_ys = [cluster.offsets[arm.id][1] for arm in beat.arms]
        columns = sum(1 for y in arm_ys if y == min(arm_ys))
        print(f"grid        {beat.id}: {columns} cols, {cluster.width}x{cluster.height}px")


def main() -> int:
    raw_groups = build_beat_groups()
    chapters = build_chapters(raw_groups)
    groups = splice_card_beats(raw_groups, chapters)
    beats = [beat for _, group_beats in groups for beat in group_beats]
    graph = build_tour_graph(beats)
    placer = build_tour_placer()
    view = placer.place(graph, beats, groups)
    steps = build_steps(groups, chapters)
    validate_tour(graph, beats, view)
    view_payload = view.model_dump()
    validate_shots(view_payload, steps, view.node_geometry)
    _print_grid_summary(placer, beats)

    payload = {
        "page_title": graph.page_title,
        "repo": graph.repo,
        "repo_url": REPO_URL,
        "view": view_payload,
        "steps": steps,
        "chapters": chapters_payload(chapters, groups, view_payload["nodes"], view.node_geometry),
    }
    TOUR_PATH.parent.mkdir(parents=True, exist_ok=True)
    TOUR_PATH.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    (OUT_DIR / "flow_graph.json").write_text(graph.model_dump_json(indent=2), encoding="utf-8")
    (OUT_DIR / "rendered_view.json").write_text(
        json.dumps(view_payload, indent=2, sort_keys=True), encoding="utf-8"
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
