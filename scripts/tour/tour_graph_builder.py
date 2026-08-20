from shared.models.flow_graph import FlowEdge, FlowGraph, FlowNode, Lane

from tour import beats_delivery, beats_gateway, beats_tracer_judge, beats_tracer_output
from tour import beats_tracer_static
from tour.tour_beat import Beat
from tour.tour_builders import node, ref

ROOT_ID = "root:codeflow"
REPO = "CodeFlow"
PAGE_TITLE = "CodeFlow - how it maps a codebase"

LANE_TITLES = {
    "gateway": "Gateway - orchestration, 8000",
    "tracer": "Tracer agent - the decision engine, 8003",
    "render": "Render agent - geometry, 8004",
    "frontend": "Frontend - progressive disclosure",
}


def build_beats() -> list[Beat]:
    return [
        *beats_gateway.beats(),
        *beats_tracer_static.beats(),
        *beats_tracer_judge.beats(),
        *beats_tracer_output.beats(),
        *beats_delivery.beats(),
    ]


def _beat_node(beat: Beat) -> FlowNode:
    return node(
        beat.id, beat.kind, beat.lane, beat.label, beat.one_liner, beat.refs,
        level=0, container=ROOT_ID, backing=beat.backing,
    )


def _arm_nodes(beat: Beat) -> list[FlowNode]:
    return [
        node(
            arm.id, arm.kind, beat.lane, arm.label, arm.note, arm.refs,
            level=0, container=ROOT_ID,
            effect_kind=arm.effect_kind, effect_target=arm.effect_target,
        )
        for arm in beat.arms
    ]


def _ordered_ids(beats: list[Beat]) -> list[str]:
    out: list[str] = []
    for beat in beats:
        out.append(beat.id)
        out.extend(arm.id for arm in beat.arms)
    return out


def _edges(beats: list[Beat]) -> list[FlowEdge]:
    out: list[FlowEdge] = []
    for index, beat in enumerate(beats):
        for arm in beat.arms:
            out.append(
                FlowEdge(source=beat.id, target=arm.id, kind="arm", arm_label=arm.arm_label)
            )
        if index + 1 >= len(beats):
            continue
        nxt = beats[index + 1].id
        converging = beat.converging()
        sources = [arm.id for arm in converging] if converging else [beat.id]
        for source in sources:
            out.append(FlowEdge(source=source, target=nxt, kind="sequence", is_spine=True))
    return out


def _lanes(beats: list[Beat]) -> list[Lane]:
    order: list[str] = []
    first: dict[str, str] = {}
    for beat in beats:
        if beat.lane not in first:
            first[beat.lane] = beat.id
            order.append(beat.lane)
    return [
        Lane(
            id=lane, name=LANE_TITLES.get(lane, lane), llm_title=LANE_TITLES.get(lane, lane),
            entry_ids=[first[lane]], mass=float(len(order) - position),
        )
        for position, lane in enumerate(order)
    ]


def build_tour_graph(beats: list[Beat]) -> FlowGraph:
    ordered = _ordered_ids(beats)
    root = node(
        ROOT_ID, "entry", ROOT_ID, REPO, "The whole pipeline, end to end.",
        (ref("PROMPT.md", 1),), level=0, children=ordered,
        body_kind="flow", body_head=beats[0].id, body_tails=[beats[-1].id],
    )
    nodes = [root]
    for beat in beats:
        nodes.append(_beat_node(beat))
        nodes.extend(_arm_nodes(beat))
    return FlowGraph(
        repo=REPO, page_title=PAGE_TITLE, lanes=_lanes(beats), nodes=nodes,
        edges=_edges(beats), meta={"tour": True},
    )
