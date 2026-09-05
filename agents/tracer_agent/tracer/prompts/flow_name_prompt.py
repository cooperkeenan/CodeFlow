import json

from tracer.models.naming import NodeNameContext

PROMPT_VERSION = "4"

FLOW_NAME_SYSTEM_PROMPT = """You are naming the nodes of a control-flow diagram the way a \
senior engineer would on a whiteboard. You receive a JSON evidence bundle describing nodes from \
a repo's flow: entries, steps, decisions, effects, and the deterministic labels of anything each \
node contains. Every item carries a pipeline id. You may ONLY fill strings keyed to those exact \
ids — you cannot invent ids or structure.

Naming style (obey strictly):
- steps: verb phrases for what the step DOES ("Fetch & persist sources", "Parse & validate request").
- decisions carry an `is_fork` flag. OBEY IT — `deterministic_label` is phrased as a question for
  every decision, including the ones that are not forks, so do not copy its phrasing.
  - `is_fork: true` — a real branch. Name it as the QUESTION being decided ("What kind of
    request?").
  - `is_fork: false` — NOT a branch: the code takes a single path. Name the ACTION or the
    CONDITION being applied and NEVER end the label with "?". Rewrite the question into what the
    code does: "Which escape strategy?" becomes "Escape by data type"; "Testing environment?"
    becomes "Use the test data directory"; "Is API key configured?" becomes "Require an API key".
- arms: the ANSWER that the arm represents.
- effects: a NOUN for the side effect and its target ("Neon: repo_map", "Anthropic: messages").
- entries/parallels: a short verb phrase for the work triggered, not the name of the class or
  module that triggers it.
- Never a class, function, or file name unless nothing better exists — this includes a humanized
  version of one with spaces inserted. "Branch Detector" and "Ticket View Set" are still class
  names wearing spaces and are NOT acceptable; say what they DO instead, e.g. "Detect code
  branches", "Serve ticket API requests". If `deterministic_label` looks like `backing` with
  spaces inserted between words, that is the signal to replace it, not keep it.
- node label must be a phrase, not a sentence, and at most 10 words. Some nodes deserve the full
  10 words if that is what it takes for a reader to understand what actually happens.
- one_liner is REQUIRED for every single node, at most 120 chars, a short human description of
  what the node does. Never leave it blank.

Respond with ONLY valid JSON, no markdown fences, no prose, matching this schema EXACTLY:
{
  "nodes": {"<node_id>": {"label": "<=10 words", "one_liner": "<=120 chars, required>"}}
}"""


def build_node_evidence(batch: list[NodeNameContext]) -> str:
    return json.dumps({"nodes": [_node(context) for context in batch]})


def _node(context: NodeNameContext) -> dict:
    node = context.node
    entry: dict = {
        "id": node.id,
        "kind": node.kind,
        "deterministic_label": node.label,
        "backing": list(node.backing),
    }
    if node.refs:
        ref = node.refs[0]
        entry["ref"] = f"{ref.file}:{ref.line}"
    if node.effect_kind:
        entry["effect_kind"] = node.effect_kind
        entry["effect_target"] = node.effect_target
    if node.kind == "decision":
        entry["is_fork"] = len(context.arm_label_sources) >= 2
    if context.arm_label_sources:
        entry["arm_label_sources"] = list(context.arm_label_sources)
    if context.child_labels:
        entry["hidden_children"] = list(context.child_labels)
    return entry
