from shared.models.flow_graph import FlowNode


def shape_for(node: FlowNode, arm_count: int) -> str:
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
    return "decision"


def node_data(
    node: FlowNode, lane_id: str, column: int, is_spine: bool, arm_count: int
) -> dict:
    dynamic = "dynamic" in node.badges
    data: dict = {
        "laneId": lane_id,
        "column": column,
        "isSpine": is_spine,
        "shape": shape_for(node, arm_count),
        "dashed": dynamic,
        "badges": list(node.badges),
        "fullLabel": node.llm_label or node.label,
        "oneLiner": node.one_liner,
        "backing": list(node.backing),
        "refs": [{"file": ref.file, "line": ref.line} for ref in node.refs],
    }
    if node.folded_count:
        data["chip"] = f"+{node.folded_count}"
        data["foldedCount"] = node.folded_count
    if node.kind == "effect":
        data["effectKind"] = node.effect_kind
        data["effectTarget"] = node.effect_target
    if dynamic:
        data["subtitle"] = "runtime dispatch"
    return data
