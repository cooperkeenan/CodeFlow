import json

from shared.models.diagram_spec import DiagramSpec
from templates.registry import TemplateRegistry

TEMPLATE_SYSTEM_PROMPT = """You choose the most appropriate diagram type for a software system \
and call select_diagram_template with your chosen type.

The tool returns either a built template (success) or a rejection with a suggested_type when \
the spec exceeds the type's node limit. If rejected, call the tool again with the suggested_type. \
Stop as soon as the tool succeeds — never call the tool more than needed.

Reason from what the system *does*, not just its graph shape. Use all available evidence:
- architecture_type: the declared architectural style — treat this as a strong prior.
- external_actors and their types: databases, browsers, webhooks signal layered or pipeline flows.
- Each module's zones list: repeated zone names across modules (e.g. presentation / domain / data \
in every module) is a reliable signal for layered_tier; varied or unique zones suggest pipeline or \
dependency_graph.
- edge_type semantics: http/event edges suggest service or event-driven boundaries; import/call \
edges are intra-process; database edges indicate storage access patterns.

Anti-artifact rule — hub_and_spoke false positives: A single entry/main/api module that calls \
many other modules is NOT by itself hub_and_spoke — that star pattern is equally common in layered \
and pipeline systems. Choose hub_and_spoke only when one module is a genuine shared coordinator \
that most other modules depend on AND the other modules are largely unconnected to each other.

Guidance for choosing:
- pipeline: strict A→B→C sequence; every module has at most one upstream and one downstream; use \
for any ordered processing chain regardless of domain; when selecting pipeline you MUST also \
supply pipeline_order — an ordered list of the stage module names in processing sequence, omitting \
utility or shared modules that are not pipeline stages
- hub_and_spoke: one module has far more connections than all others; spokes have few or no edges \
between themselves; the hub is a coordinator or shared dependency
- layered_tier: modules cluster into horizontal responsibility bands (e.g. intake / processing / \
storage); traffic only flows downward across tier boundaries; multiple modules may share a tier; \
uniform zone structure across modules strongly supports this choice
- hierarchy: tree-shaped ownership; a root delegates to children who may delegate further; use \
when the primary relationship is containment or delegation, not sequential flow
- dependency_graph: edges run in multiple directions with no single dominant hub or strict \
sequence; use to show actual import or call-dependency structure
- mesh: terminal fallback only; use when no other type captures the edge pattern"""


def build_evidence(spec: DiagramSpec, registry: TemplateRegistry) -> str:
    modules = [
        {
            "name": m.name,
            "description": m.purpose or m.description,
            "primary_components": [
                {"name": c.name, "role": c.role}
                for comps in m.zones.values()
                for c in comps
                if c.tier == "primary" and c.role
            ],
            "zone_count": len(m.zones),
            "zones": list(m.zones.keys()),
        }
        for m in spec.modules
    ]
    comp_to_mod: dict[str, str] = {
        c.name: m.name
        for m in spec.modules
        for comps in m.zones.values()
        for c in comps
    }
    seen: set[tuple[str, str]] = set()
    module_edges: list[dict] = []
    for e in spec.edges:
        src, tgt = comp_to_mod.get(e.source), comp_to_mod.get(e.target)
        if src and tgt and src != tgt and (src, tgt) not in seen:
            seen.add((src, tgt))
            module_edges.append({"source": src, "target": tgt, "edge_type": e.edge_type})
    options = [
        {"type": t, "description": d, "node_limit": lim}
        for t, d, lim in registry.descriptions()
    ]
    return json.dumps(
        {
            "architecture_type": spec.architecture_type,
            "external_actors": [
                {"name": a.name, "type": a.type, "description": a.description}
                for a in spec.external_actors
            ],
            "modules": modules,
            "module_edges": module_edges,
            "entry_points": spec.entry_points,
            "template_options": options,
        },
        indent=2,
    )
