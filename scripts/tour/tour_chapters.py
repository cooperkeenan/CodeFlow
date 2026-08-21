from dataclasses import dataclass

from tour.tour_beat import Beat

_CHAPTER_META: tuple[tuple[str, str, str], ...] = (
    (
        "gateway",
        "Taking the request",
        "One HTTP entry point decides whether this repo has been seen before, "
        "then fans the work out to four services.",
    ),
    (
        "static",
        "Reading the code",
        "Static analysis builds a symbol table, resolves every call, and turns "
        "each branch point into a candidate decision.",
    ),
    (
        "judge",
        "Deciding what matters",
        "The only stage an LLM touches: it judges which forks a human would "
        "actually put on a mental model, and never rewires the graph.",
    ),
    (
        "output",
        "Making it fit",
        "Condense to a graph, stitch the services together, and demote detail "
        "to a deeper level rather than deleting it.",
    ),
    (
        "delivery",
        "Drawing it",
        "The server owns geometry; the browser is a thin renderer with "
        "progressive disclosure.",
    ),
)


@dataclass(frozen=True)
class Chapter:
    id: str
    number: int
    title: str
    thesis: str
    beat_ids: tuple[str, ...]


def build_chapters(groups: list[tuple[str, list[Beat]]]) -> list[Chapter]:
    if len(groups) != len(_CHAPTER_META):
        raise ValueError(
            f"expected {len(_CHAPTER_META)} beat groups for chapters, got {len(groups)}"
        )
    return [
        Chapter(
            id=chapter_id,
            number=index + 1,
            title=title,
            thesis=thesis,
            beat_ids=tuple(beat.id for beat in beats),
        )
        for index, ((chapter_id, title, thesis), (_, beats)) in enumerate(
            zip(_CHAPTER_META, groups)
        )
    ]


def _bounds(node_ids: list[str], positions: dict[str, dict], geometry: dict) -> dict[str, int]:
    boxes = [positions[node_id] for node_id in node_ids if node_id in positions]
    lefts = [box["position"]["x"] for box in boxes]
    tops = [box["position"]["y"] for box in boxes]
    rights = [box["position"]["x"] + geometry[box["shape"]]["width"] for box in boxes]
    bottoms = [box["position"]["y"] + geometry[box["shape"]]["height"] for box in boxes]
    return {"minX": min(lefts), "minY": min(tops), "maxX": max(rights), "maxY": max(bottoms)}


def chapters_payload(
    chapters: list[Chapter],
    spliced_groups: list[tuple[str, list[Beat]]],
    view_nodes: list[dict],
    geometry: dict[str, dict[str, int]],
) -> list[dict]:
    positions = {item["id"]: item for item in view_nodes}
    out = []
    for chapter, (_, beats) in zip(chapters, spliced_groups):
        step_ids = [beat.id for beat in beats]
        node_ids = [nid for beat in beats for nid in [beat.id, *(arm.id for arm in beat.arms)]]
        out.append(
            {
                "id": chapter.id,
                "number": chapter.number,
                "title": chapter.title,
                "thesis": chapter.thesis,
                "stepIds": step_ids,
                "bounds": _bounds(node_ids, positions, geometry),
            }
        )
    return out
