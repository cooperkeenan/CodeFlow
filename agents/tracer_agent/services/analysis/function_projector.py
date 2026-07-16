from collections.abc import Callable

from models.dispatch_site import DispatchSite
from models.effect_site import EffectSite
from models.flow_summary import FlowSummary
from models.parallel_site import ParallelSite
from models.project_index import ProjectIndex
from shared.models.flow_graph import Badge, SourceRef

from services.analysis.anchor_index import AnchorIndex
from services.analysis.chain_builder import ChainBuilder
from services.analysis.collected_events import CollectedEvents
from services.analysis.flow_event import FlowEvent
from services.analysis.graph_accumulator import GraphAccumulator
from services.analysis.label_synthesizer import LabelSynthesizer

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
            self._handle_call(chain, events, item)
        elif item.kind == "effect":
            self._attach_effect(chain, item.payload, set())
        elif item.kind == "parallel":
            self._handle_parallel(chain, item.payload)
        else:
            self._handle_decision(chain, fqn, events, prefix, item.payload)

    def _handle_call(self, chain: ChainBuilder, events: CollectedEvents, item: FlowEvent) -> None:
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
                chain.splice(summary.head, summary.tails, badges | loop)
        for effect in self._boundary_effects(call.targets):
            self._attach_effect(chain, effect, badges)

    def _boundary_effects(self, targets: tuple) -> tuple[EffectSite, ...]:
        seen: dict[str, EffectSite] = {}
        for target in targets:
            for effect in self._anchors.boundary_effects(target.fqn):
                seen[effect.id] = effect
        return tuple(sorted(seen.values(), key=lambda e: e.id))

    def _attach_effect(self, chain: ChainBuilder, effect: EffectSite, badges: set[Badge]) -> None:
        self._acc.upsert(
            effect.id, "effect", chain.lane, self._labels.effect_label(effect.kind, effect.target),
            refs=[self._effect_ref(effect)], badges=set(badges),
            effect_kind=effect.kind, effect_target=effect.target,
        )
        chain.attach(effect.id)

    def _effect_ref(self, effect: EffectSite) -> SourceRef:
        record = self._index.classes.get(effect.owner) or self._index.functions.get(effect.owner)
        file = record.span.file if record is not None else ""
        return SourceRef(file=file, line=effect.line, end_line=effect.line)

    def _handle_parallel(self, chain: ChainBuilder, site: ParallelSite) -> None:
        self._acc.upsert(site.id, "parallel", chain.lane, "Parallel")
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
        node_id = f"dec:{site.id}"
        self._acc.upsert(node_id, "decision", chain.lane, self._labels.decision_label(site.selector_source))
        chain.attach(node_id)
        tails: list[str] = []
        for arm in site.arms:
            ahead, atails = self._build_region(fqn, events, prefix + ((site.id, arm.index),), chain.lane)
            if ahead is None:
                tails.append(node_id)
            else:
                self._acc.connect(node_id, ahead, "arm", arm.label_source, site.id)
                tails.extend(atails or [ahead])
        chain.fan_out(node_id, _dedup(tails))


def _dedup(values: list[str]) -> list[str]:
    seen: dict[str, None] = {}
    for value in values:
        seen.setdefault(value, None)
    return list(seen)
