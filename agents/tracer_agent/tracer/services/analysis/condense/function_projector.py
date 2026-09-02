from collections.abc import Callable

from tracer.models.flow_summary import FlowSummary
from tracer.models.index_records import ProjectIndex
from tracer.models.sites import DispatchSite, EffectSite, ParallelSite
from tracer.services.analysis.condense.anchor_index import AnchorIndex
from tracer.services.analysis.condense.chain_builder import ChainBuilder
from tracer.services.analysis.condense.decision_projector import DecisionProjector
from tracer.services.analysis.condense.drafts import CollectedEvents, FlowEvent
from tracer.services.analysis.condense.graph_accumulator import GraphAccumulator
from tracer.services.analysis.condense.labels import DecisionLabeler, OutcomeLabeler
from tracer.services.analysis.routes.label_synthesizer import LabelSynthesizer

from shared.models.flow_graph import Badge, SourceRef

_Path = tuple[tuple[str, int], ...]


class FunctionProjector:
    def __init__(
        self,
        index: ProjectIndex,
        anchors: AnchorIndex,
        acc: GraphAccumulator,
        labels: LabelSynthesizer,
        summarize: Callable[[str], FlowSummary],
    ) -> None:
        self._index = index
        self._anchors = anchors
        self._acc = acc
        self._labels = labels
        self._summarize = summarize
        self._decisions = DecisionProjector(
            anchors, acc, DecisionLabeler(labels), OutcomeLabeler()
        )

    def project(self, fqn: str, events: CollectedEvents, lane: str) -> FlowSummary:
        head, tails = self._build_region(fqn, events, (), lane)
        return FlowSummary(head, tuple(tails))

    def _build_region(
        self, fqn: str, events: CollectedEvents, prefix: _Path, lane: str
    ) -> tuple[str | None, list[str]]:
        chain = ChainBuilder(self._acc, self._labels, fqn, lane)
        items = [e for e in events.leaves if e.path == prefix]
        items += [d for d in events.decisions if events.decision_prefix[d.payload.id] == prefix]
        for item in sorted(items, key=lambda e: e.sort_key):
            self._handle(chain, fqn, events, prefix, item)
        return chain.head, chain.frontier

    def _handle(
        self, chain: ChainBuilder, fqn: str, events: CollectedEvents, prefix: _Path, item: FlowEvent
    ) -> None:
        if item.kind == "call":
            self._handle_call(chain, fqn, prefix, events, item)
        elif item.kind == "effect":
            self._attach_effect(chain, fqn, prefix, item.payload, set())
        elif item.kind == "parallel":
            self._handle_parallel(chain, fqn, item.payload)
        else:
            self._handle_decision(chain, fqn, events, prefix, item.payload)

    def _handle_call(
        self, chain: ChainBuilder, fqn: str, prefix: _Path, events: CollectedEvents, item: FlowEvent
    ) -> None:
        call = item.payload
        badges: set[Badge] = set()
        if any(frame.site_id in events.guarded_ids for frame in call.context):
            badges.add("guarded")
        ref = SourceRef(file=events.file, line=call.line, end_line=call.line)
        proj = [t for t in call.targets if self._anchors.is_project_function(t.fqn)]
        if proj:
            summary = self._summarize(proj[0].fqn)
            loop = {"loop"} if call.in_loop else set()
            if summary.head is None:
                extra: set[Badge] = {"recursive"} if summary.recursive else set()
                chain.add_backing(proj[0].fqn, ref, badges | extra)
            else:
                self._acc.record_call_boundary(fqn, self._local_container(prefix), proj[0].fqn)
                chain.splice(summary.head, summary.tails, badges | loop)
        for effect in self._boundary_effects(call.targets):
            self._attach_effect(chain, fqn, prefix, effect, badges)

    def _local_container(self, prefix: _Path) -> str:
        return f"dec:{prefix[-1][0]}" if prefix else ""

    def _boundary_effects(self, targets: tuple) -> tuple[EffectSite, ...]:
        seen: dict[str, EffectSite] = {}
        for target in targets:
            for effect in self._anchors.boundary_effects(target.fqn):
                seen[effect.id] = effect
        return tuple(sorted(seen.values(), key=lambda e: e.id))

    def _attach_effect(
        self, chain: ChainBuilder, fqn: str, prefix: _Path, effect: EffectSite, badges: set[Badge]
    ) -> None:
        self._acc.upsert(
            effect.id, "effect", chain.lane, self._labels.effect_label(effect.kind, effect.target),
            refs=[self._effect_ref(effect)], badges=set(badges),
            effect_kind=effect.kind, effect_target=effect.target,
        )
        self._acc.set_owner(effect.id, effect.owner, [])
        self._acc.record_effect_boundary(fqn, self._local_container(prefix), effect.id)
        chain.attach(effect.id)

    def _effect_ref(self, effect: EffectSite) -> SourceRef:
        record = self._index.classes.get(effect.owner) or self._index.functions.get(effect.owner)
        file = record.span.file if record is not None else ""
        return SourceRef(file=file, line=effect.line, end_line=effect.line)

    def _handle_parallel(self, chain: ChainBuilder, fqn: str, site: ParallelSite) -> None:
        self._acc.upsert(site.id, "parallel", chain.lane, "Parallel", refs=[site.span])
        self._acc.set_owner(site.id, fqn, [])
        chain.attach(site.id)
        tails: list[str] = []
        for callee in site.callees:
            summary = self._summarize(callee)
            if summary.head is not None:
                self._acc.connect(site.id, summary.head, "parallel")
                tails.extend(summary.tails or (summary.head,))
        chain.fan_out(site.id, _dedup(tails))

    def _handle_decision(
        self, chain: ChainBuilder, fqn: str, events: CollectedEvents, prefix: _Path, site: DispatchSite
    ) -> None:
        self._decisions.handle(self._build_region, chain, fqn, events, prefix, site)

def _dedup(values: list[str]) -> list[str]:
    seen: dict[str, None] = {}
    for value in values:
        seen.setdefault(value, None)
    return list(seen)
