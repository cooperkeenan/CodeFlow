import json

COMPONENT_TYPE_SYSTEM_PROMPT = """You classify high-level software components by their internal
structure, choosing the DiagramType that best conveys how the component coordinates its work.

You are given a list of high-level components with their rich descriptions, callers, callees, and
children. For each component, choose the most appropriate type and explain why in one sentence.
When the chosen type has a natural execution order (pipeline or hierarchy), also return the ordered
node sequence.

Return ONLY valid JSON with no markdown fences, no explanation, matching this schema exactly:
{
  "components": {
    "<component name>": {
      "type": "<pipeline|hub_and_spoke|hierarchy|dependency_graph|relationship>",
      "reasoning": "<one sentence why this type fits>",
      "order": ["<node id in execution order>"]
    }
  }
}

Omit "order" for non-sequential types (hub_and_spoke, dependency_graph, relationship).
Include "order" only for pipeline (left-to-right chain) and hierarchy (top-down tree).

TYPE GUIDANCE:
- pipeline: the component runs its callees/children in a clear step-by-step order (e.g. fetch →
  build → validate → assemble). "order" MUST list ALL callee and children node ids in execution
  sequence — every callee/child must appear exactly once.
- hub_and_spoke: only when the component dispatches to MANY (4 or more) INDEPENDENT services/APIs
  in DIFFERENT modules (typically via HTTP cross-service calls) and those spokes do not call each
  other; NOT for a service that calls a few internal helpers.
- hierarchy: the component branches to several tools/children — a decision/branch ("call this tool
  or that tool") — or a containment tree; use for parent-to-children branching. "order" lists ALL
  nodes top-down.
- dependency_graph: mixed or bidirectional dependencies, no dominant single pattern.
- relationship: the component has ≤1 callee/child; show it in context of its callers.

Use temperature 0; be deterministic. Only include components that appear in the input. Every
component in the input MUST appear in the output."""


def build_component_evidence(components: list[dict]) -> str:
    return json.dumps({"components": components}, indent=2)
