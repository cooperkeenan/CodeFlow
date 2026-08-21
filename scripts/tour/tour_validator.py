from shared.models.flow_graph import FlowGraph

from tour.tour_beat import Beat


class TourValidationError(Exception):
    pass


def _fail(message: str) -> None:
    raise TourValidationError(message)


def _check_edges(graph: FlowGraph) -> None:
    ids = {node.id for node in graph.nodes}
    for edge in graph.edges:
        if edge.source not in ids:
            _fail(f"edge from unknown node {edge.source}")
        if edge.target not in ids:
            _fail(f"edge to unknown node {edge.target}")


def _check_containment(graph: FlowGraph) -> None:
    ids = {node.id for node in graph.nodes}
    children = {node.id: list(node.hidden_children) for node in graph.nodes}
    roots = sorted(node.id for node in graph.nodes if not node.containers)
    if len(roots) != 1:
        _fail(f"expected exactly one containment root, got {roots}")
    for node in graph.nodes:
        for container in node.containers:
            if container not in ids:
                _fail(f"{node.id} has unknown container {container}")
            elif node.id not in children[container]:
                _fail(f"{node.id} claims container {container} which does not list it")
    reached = set(children[roots[0]]) | {roots[0]}
    missing = sorted(ids - reached)
    if missing:
        _fail(f"{len(missing)} nodes unreachable from {roots[0]}: {missing[:5]}")


def _check_main_line(beats: list[Beat], graph: FlowGraph) -> None:
    pairs = {(edge.source, edge.target) for edge in graph.edges}
    arm_owner = {arm.id: beat.id for beat in beats for arm in beat.arms}
    for index in range(len(beats) - 1):
        beat, nxt = beats[index], beats[index + 1]
        sources = [arm.id for arm in beat.converging()] or [beat.id]
        for source in sources:
            if (source, nxt.id) not in pairs:
                _fail(f"main line broken between {beat.id} and {nxt.id}")
    for beat in beats:
        for arm in beat.arms:
            if (beat.id, arm.id) not in pairs:
                _fail(f"{beat.id} does not reach its arm {arm.id}")
            if arm_owner[arm.id] != beat.id:
                _fail(f"arm {arm.id} is claimed by two beats")


def _check_decisions(beats: list[Beat]) -> None:
    for beat in beats:
        if beat.kind == "decision" and len(beat.arms) < 2:
            _fail(f"decision {beat.id} has {len(beat.arms)} arms, needs at least 2")
        if beat.kind != "decision" and beat.converging():
            _fail(f"{beat.id} is not a decision but has converging arms")


def _check_narration(beats: list[Beat]) -> None:
    seen: set[str] = set()
    for beat in beats:
        if beat.id in seen:
            _fail(f"duplicate beat id {beat.id}")
        seen.add(beat.id)
        if not beat.title or not beat.body:
            _fail(f"beat {beat.id} is missing narration")
        if not beat.refs:
            _fail(f"beat {beat.id} has no source refs")


def _check_packets(beats: list[Beat], graph: FlowGraph) -> None:
    pairs = {f"{edge.source}->{edge.target}" for edge in graph.edges}
    for beat in beats:
        for packet in beat.packets:
            if packet not in pairs:
                _fail(f"beat {beat.id} animates unknown edge {packet}")


def _check_overlaps(view_nodes: list[dict], geometry: dict) -> None:
    boxes = []
    for item in view_nodes:
        size = geometry[item["shape"]]
        pos = item["position"]
        boxes.append((item["id"], pos["x"], pos["y"], size["width"], size["height"]))
    for i in range(len(boxes)):
        aid, ax, ay, aw, ah = boxes[i]
        for j in range(i + 1, len(boxes)):
            bid, bx, by, bw, bh = boxes[j]
            if ax < bx + bw and bx < ax + aw and ay < by + bh and by < ay + ah:
                _fail(f"nodes overlap: {aid} and {bid}")


def validate_tour(graph: FlowGraph, beats: list[Beat], view) -> None:
    _check_edges(graph)
    _check_containment(graph)
    _check_main_line(beats, graph)
    _check_decisions(beats)
    _check_narration(beats)
    _check_packets(beats, graph)
    _check_overlaps(view.nodes, view.node_geometry)
