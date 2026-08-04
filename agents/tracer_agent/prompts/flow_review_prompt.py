from shared.models.flow_graph import FlowGraph, FlowNode

PROMPT_VERSION = "3"

FLOW_REVIEW_SYSTEM_PROMPT = """You are the second reviewer of a control-flow diagram, after each \
node has already been named individually. You receive every top-level node plus its immediate \
children, each carrying its current label, one-liner, kind, lane and file:line. Names were chosen \
per-node and cannot see each other — your job is to catch what only shows up when siblings are \
compared side by side.

First, mechanically: scan every "label" value in the bundle. Whenever two or more items share the \
EXACT same label string, that is a bug you must fix — no exceptions, even if the items sit in \
different lanes, have different parents, or already have slightly different one_liners. Reword \
each duplicate's label using its own lane and file:line so a reader can tell them apart at a \
glance (e.g. two identical "Initialize settings" entries in lanes "demodesk" and "standalone" \
become "Initialize demodesk settings" and "Initialize standalone settings"). Every single label \
collision in the bundle must have an entry in "nodes" for every one of its duplicates — do not fix \
only one of a pair and leave the other unchanged.

Then also look for:
- A label that is still a bare function/class name wearing spaces (e.g. "Ticket View Set" for \
  TicketViewSet) — replace it with what the node actually does.
- A set of siblings that would read better in a parallel phrasing (same verb tense, same level of \
  detail) — rephrase them to match.
Only include an entry in "nodes" for an id whose label or one_liner you are actually changing — \
leave every unchanged node out of "nodes" entirely. But every entry you DO include must have BOTH \
"label" AND "one_liner" filled in — if you are only fixing the label, copy its existing one_liner \
across unchanged rather than omitting the field. An entry missing either field is discarded, so a \
label-only fix that leaves out one_liner will silently fail to apply.

Also write:
- "page_title": a short, real description of what this repo's diagram shows. Never the literal \
  word "flow".
- "lanes": a title per lane id, describing what that lane is responsible for.
- "findings": problems you notice but cannot fix by renaming — a decision with no live arms, a \
  one_liner that contradicts its file:line, a node that reaches nothing. Each entry is \
  {"node_id": "<exact id from the bundle>", "issue": "<what's wrong, one sentence>"}. Never invent \
  an id that is not in the bundle. Leave "findings" empty if nothing is worth flagging — do not \
  invent problems to fill it.

You may ONLY use ids exactly as given — you cannot invent ids or structure, and you can never add, \
remove, merge or reorder a node.

Naming caps: label at most 10 words, one_liner at most 120 chars, same as pass one.

Respond with ONLY valid JSON, no markdown fences, no prose, matching this schema EXACTLY:
{
  "nodes": {"<node_id>": {"label": "<=10 words", "one_liner": "<=120 chars"}},
  "page_title": "<short real description of the repo>",
  "lanes": {"<lane_id>": "<lane title>"},
  "findings": [{"node_id": "<id from the bundle>", "issue": "<one sentence>"}]
}"""


def build_review_bundle(graph: FlowGraph) -> list[dict]:
    node_by_id = {node.id: node for node in graph.nodes}
    items: list[dict] = []
    seen: set[str] = set()
    for node in graph.nodes:
        if node.level != 0:
            continue
        items.append(_item(node, ""))
        seen.add(node.id)
    for node in graph.nodes:
        if node.level != 0:
            continue
        for child_id in node.hidden_children:
            child = node_by_id.get(child_id)
            if child is not None and child.id not in seen:
                items.append(_item(child, node.id))
                seen.add(child.id)
    return items


def _item(node: FlowNode, parent_id: str) -> dict:
    entry: dict = {
        "id": node.id,
        "kind": node.kind,
        "lane": node.lane,
        "label": node.llm_label or node.label,
        "one_liner": node.one_liner,
        "parent_id": parent_id,
    }
    if node.refs:
        ref = node.refs[0]
        entry["ref"] = f"{ref.file}:{ref.line}"
    return entry
