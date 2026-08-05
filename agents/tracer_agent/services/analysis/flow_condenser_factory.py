from services.analysis.flow_condenser import FlowCondenser
from services.analysis.label_synthesizer import LabelSynthesizer
from services.analysis.service_root_resolver import ServiceRootResolver


def build_flow_condenser(
    service_hints: frozenset[str] | None = None,
    source_roots: frozenset[str] = frozenset(),
) -> FlowCondenser:
    return FlowCondenser(ServiceRootResolver(service_hints, source_roots), LabelSynthesizer())
