from os.path import basename

from shared.models.flow_graph import FlowGraph, FlowNode


def is_linear(node: FlowNode, arm_count: int) -> bool:
    return node.kind == "decision" and arm_count <= 1


def linear_run_ids(graph: FlowGraph, arm_counts: dict[str, int]) -> frozenset[str]:
    nodes_by_id = {n.id: n for n in graph.nodes}
    chained = {(edge.source, edge.target) for edge in graph.edges if edge.kind == "sequence"}
    run: set[str] = set()
    for owner in graph.nodes:
        members = [nodes_by_id[c] for c in owner.hidden_children if c in nodes_by_id]
        flags = [is_linear(m, arm_counts.get(m.id, 0)) for m in members]
        for index, flagged in enumerate(flags):
            if not flagged:
                continue
            before = (
                index > 0 and flags[index - 1]
                and (members[index - 1].id, members[index].id) in chained
            )
            after = (
                index + 1 < len(flags) and flags[index + 1]
                and (members[index].id, members[index + 1].id) in chained
            )
            if before or after:
                run.add(members[index].id)
    return frozenset(run)


def shape_for(node: FlowNode, arm_count: int, in_run: bool = False) -> str:
    if node.kind == "entry":
        return "pill"
    if node.kind == "step":
        return "rect"
    if node.kind == "parallel":
        return "split_bar"
    if node.kind == "effect":
        return "effect"
    if node.kind == "outcome":
        return "outcome"
    if node.kind == "decision" and is_linear(node, arm_count):
        return "pipeline" if in_run else "rect"
    return "decision"


def node_data(
    node: FlowNode, lane_id: str, column: int, is_spine: bool, arm_count: int,
    in_run: bool = False,
) -> dict:
    dynamic = "dynamic" in node.badges
    linear = is_linear(node, arm_count)
    data: dict = {
        "laneId": lane_id,
        "column": column,
        "isSpine": is_spine,
        "shape": shape_for(node, arm_count, in_run),
        "dashed": dynamic,
        "badges": list(node.badges),
        "fullLabel": node.llm_label or node.label,
        "oneLiner": node.one_liner,
        "backing": list(node.backing),
        "refs": [{"file": ref.file, "line": ref.line} for ref in node.refs],
    }
    if node.refs:
        data["provenance"] = f"{basename(node.refs[0].file)}:{node.refs[0].line}"
    if linear:
        data["linear"] = True
    if node.body_head:
        data["bodyHead"] = node.body_head
    if node.body_tails:
        data["bodyTails"] = list(node.body_tails)
    if node.folded_count:
        data["chip"] = f"+{node.folded_count}"
        data["foldedCount"] = node.folded_count
    if node.kind == "effect":
        data["effectKind"] = node.effect_kind
        data["effectTarget"] = node.effect_target
    if dynamic:
        data["subtitle"] = "runtime dispatch"
    return data
