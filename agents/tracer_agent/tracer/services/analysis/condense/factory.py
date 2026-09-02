from tracer.services.analysis.condense.flow_condenser import FlowCondenser
from tracer.services.analysis.indexing.service_root_resolver import ServiceRootResolver
from tracer.services.analysis.routes.label_synthesizer import LabelSynthesizer


def build_flow_condenser(
    service_hints: frozenset[str] | None = None,
    source_roots: frozenset[str] = frozenset(),
) -> FlowCondenser:
    return FlowCondenser(ServiceRootResolver(service_hints, source_roots), LabelSynthesizer())
