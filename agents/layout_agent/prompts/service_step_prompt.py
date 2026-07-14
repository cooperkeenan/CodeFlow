import json

from shared.models.diagram_spec import Component, Edge, Module

SERVICE_STEP_SYSTEM_PROMPT = """You are given ONE leaf service module: its name, components \
(name, role, tier, description), and intra-module edges.

Do three things:
(a) Infer the service's PURPOSE in one sentence.
(b) Choose the single best diagram_type from exactly: pipeline | hub_and_spoke | hierarchy | dependency_graph
    - pipeline: ordered stage chain where data flows step-to-step in a defined sequence
    - hub_and_spoke: one central dispatcher coordinates independent, unordered handlers
    - hierarchy: a parent component delegates to child helpers
    - dependency_graph: mixed or no dominant pattern (use when nothing else fits)
(c) Break the service into AT MOST 8 MEANINGFUL steps described by what they DO \
(e.g. "Fetch & traverse codebase", "Gather traversal evidence"), NOT class or file names. \
Each step MUST include backing_components: the exact component name(s) from the input it maps to. \
Every PRIMARY component (tier="primary") must be covered by exactly one step. \
Order steps in execution order via integer order_index starting at 0.

Respond with ONLY valid JSON, no markdown fences, no explanation, matching this schema exactly:
{
  "purpose": "<one sentence describing what this service does>",
  "diagram_type": "<pipeline|hub_and_spoke|hierarchy|dependency_graph>",
  "steps": [
    {
      "label": "<short action phrase>",
      "description": "<one sentence of what this step does>",
      "backing_components": ["<exact component name from input>"],
      "order_index": 0
    }
  ]
}"""


def build_service_evidence(
    module: Module, components: list[Component], edges: list[Edge]
) -> str:
    comp_dicts = [
        {"name": c.name, "role": c.role, "tier": c.tier, "description": c.description}
        for c in components
    ]
    edge_dicts = [
        {"source": e.source, "target": e.target, "edge_type": e.edge_type}
        for e in edges
    ]
    return json.dumps({"module": module.name, "components": comp_dicts, "edges": edge_dicts})
