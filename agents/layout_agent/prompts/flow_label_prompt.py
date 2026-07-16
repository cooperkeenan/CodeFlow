import json

from shared.models.flow_graph import FlowEdge, FlowGraph, FlowNode, Lane

FLOW_LABEL_SYSTEM_PROMPT = """You are naming the nodes of a control-flow diagram the way a \
senior engineer would on a whiteboard. You receive a JSON evidence bundle describing a repo's \
flow: lanes, entries, steps, decisions, decision arms, and effects. Every item carries a pipeline \
id. You may ONLY fill strings keyed to those exact ids — you cannot invent ids or structure.

Naming style (obey strictly):
- steps: verb phrases for what the step DOES ("Fetch & persist sources", "Parse & validate request").
- decisions: the QUESTION being decided ("What kind of request?").
- arms: the ANSWER that the arm represents ("CPT question", "LLM failed").
- effects: a NOUN for the side effect and its target ("Neon: repo_map", "Anthropic: messages").
- entries/parallels: a short verb phrase for the work triggered.
- Never a class, function, or file name unless nothing better exists.
- node label ≤ 6 words; one_liner ≤ 120 chars; arm ≤ 4 words; titles short.

Respond with ONLY valid JSON, no markdown fences, no prose, matching this schema EXACTLY:
{
  "page_title": "<short title for the whole diagram>",
  "lanes": {"<lane_id>": "<short lane title>"},
  "nodes": {"<node_id>": {"label": "<=6 words", "one_liner": "<=120 chars>"}},
  "arms": {"<group_id>#<arm_index>": "<=4 words>"}
}"""


def arm_key_map(graph: FlowGraph) -> dict[str, FlowEdge]:
    counters: dict[str, int] = {}
    keyed: dict[str, FlowEdge] = {}
    for edge in graph.edges:
        if edge.kind != "arm":
            continue
        index = counters.get(edge.group_id, 0)
        counters[edge.group_id] = index + 1
        keyed[f"{edge.group_id}#{index}"] = edge
    return keyed


def build_flow_evidence(graph: FlowGraph) -> str:
    arms_by_source: dict[str, list[tuple[str, FlowEdge]]] = {}
    for key, edge in arm_key_map(graph).items():
        arms_by_source.setdefault(edge.source, []).append((key, edge))
    payload = {
        "repo": graph.repo,
        "lanes": [_lane(lane) for lane in graph.lanes],
        "entries": [_node(n) for n in graph.nodes if n.kind in ("entry", "parallel")],
        "steps": [_node(n) for n in graph.nodes if n.kind == "step"],
        "decisions": [_decision(n, arms_by_source) for n in graph.nodes if n.kind == "decision"],
        "effects": [_effect(n) for n in graph.nodes if n.kind == "effect"],
    }
    architecture = graph.meta.get("architecture")
    if isinstance(architecture, str) and architecture:
        payload["architecture"] = architecture
    return json.dumps(payload)


def _lane(lane: Lane) -> dict:
    return {"id": lane.id, "name": lane.name, "entries": list(lane.entry_ids)}


def _node(node: FlowNode) -> dict:
    return {
        "id": node.id,
        "kind": node.kind,
        "lane": node.lane,
        "deterministic_label": node.label,
        "backing": list(node.backing),
    }


def _decision(node: FlowNode, arms_by_source: dict[str, list[tuple[str, FlowEdge]]]) -> dict:
    arms = [
        {"key": key, "label_source": edge.arm_label, "target": edge.target}
        for key, edge in arms_by_source.get(node.id, [])
    ]
    return {
        "id": node.id,
        "lane": node.lane,
        "selector_source": node.label,
        "backing": list(node.backing),
        "arms": arms,
    }


def _effect(node: FlowNode) -> dict:
    return {
        "id": node.id,
        "lane": node.lane,
        "deterministic_label": node.label,
        "effect_kind": node.effect_kind,
        "effect_target": node.effect_target,
    }
