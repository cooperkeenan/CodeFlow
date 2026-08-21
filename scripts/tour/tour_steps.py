from tour.tour_beat import Beat
from tour.tour_chapters import Chapter
from tour.tour_dwell import dwell_for
from tour.tour_graph_builder import LANE_TITLES
from tour.tour_shots import default_shot

PHASE_NAMES = {
    "gateway": "Gateway",
    "tracer": "Tracer agent",
    "render": "Render agent",
    "frontend": "Frontend",
}


def _branches(beat: Beat) -> list[dict]:
    return [
        {
            "label": arm.arm_label,
            "target": arm.label,
            "note": arm.note,
            "terminal": arm.terminal,
        }
        for arm in beat.arms
    ]


def _refs(beat: Beat) -> list[dict]:
    return [{"file": item.file, "line": item.line} for item in beat.refs]


def build_steps(
    groups: list[tuple[str, list[Beat]]], chapters: list[Chapter],
) -> list[dict]:
    steps = []
    index = 0
    for chapter, (_, beats) in zip(chapters, groups):
        for chapter_position, beat in enumerate(beats, start=1):
            focus = [beat.id] + [arm.id for arm in beat.arms]
            steps.append(
                {
                    "id": beat.id,
                    "title": beat.title,
                    "body": beat.body,
                    "detail": beat.detail,
                    "phase": PHASE_NAMES.get(beat.lane, beat.lane),
                    "phaseTitle": LANE_TITLES.get(beat.lane, beat.lane),
                    "focus": focus,
                    "anchor": beat.id,
                    "packets": list(beat.packets),
                    "node": {
                        "label": beat.label,
                        "kind": beat.kind,
                        "oneLiner": beat.one_liner,
                        "backing": list(beat.backing),
                        "refs": _refs(beat),
                    },
                    "branches": _branches(beat),
                    "facts": [{"label": key, "value": value} for key, value in beat.facts],
                    "position": index + 1,
                    "shot": beat.shot or default_shot(beat),
                    "dwellMs": dwell_for(beat),
                    "chapter": chapter.id,
                    "chapterPosition": chapter_position,
                }
            )
            index += 1
    return steps
