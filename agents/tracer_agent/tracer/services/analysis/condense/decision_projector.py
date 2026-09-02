from collections.abc import Callable

from tracer.models.call_records import Arm
from tracer.models.sites import DispatchSite
from tracer.models.verdicts import SiteVerdict
from tracer.services.analysis.condense.anchor_index import AnchorIndex
from tracer.services.analysis.condense.chain_builder import ChainBuilder
from tracer.services.analysis.condense.drafts import CollectedEvents
from tracer.services.analysis.condense.graph_accumulator import GraphAccumulator
from tracer.services.analysis.condense.labels import DecisionLabeler, OutcomeLabeler

_Path = tuple[tuple[str, int], ...]
_BuildRegion = Callable[[str, CollectedEvents, _Path, str], tuple[str | None, list[str]]]


class DecisionProjector:
    def __init__(
        self,
        anchors: AnchorIndex,
        acc: GraphAccumulator,
        decision_labels: DecisionLabeler,
        outcome_labels: OutcomeLabeler,
    ) -> None:
        self._anchors = anchors
        self._acc = acc
        self._decision_labels = decision_labels
        self._outcome_labels = outcome_labels

    def handle(
        self,
        build_region: _BuildRegion,
        chain: ChainBuilder,
        fqn: str,
        events: CollectedEvents,
        prefix: _Path,
        site: DispatchSite,
    ) -> None:
        node_id = f"dec:{site.id}"
        verdict = self._anchors.site_verdict(site.id)
        label = self._decision_labels.decision_label(site, verdict)
        self._acc.upsert(node_id, "decision", chain.lane, label, refs=[site.span])
        self._acc.set_owner(node_id, fqn, [f"{s}#{i}" for s, i in prefix])
        chain.attach(node_id)
        tails: list[str] = []
        for arm in site.arms:
            ahead, atails = build_region(fqn, events, prefix + ((site.id, arm.index),), chain.lane)
            arm_label = self._decision_labels.arm_label(arm, verdict)
            if ahead is None:
                if arm.terminal == "falls_through":
                    tails.append(node_id)
                else:
                    self._acc.add_badge(node_id, "guarded")
                    self._emit_outcome(chain.lane, node_id, fqn, prefix, site, arm, verdict)
            else:
                self._acc.connect(node_id, ahead, "arm", arm_label, site.id)
                tails.extend(atails or [ahead])
        chain.fan_out(node_id, _dedup(tails))

    def _emit_outcome(
        self,
        lane: str,
        node_id: str,
        fqn: str,
        prefix: _Path,
        site: DispatchSite,
        arm: Arm,
        verdict: SiteVerdict | None,
    ) -> None:
        outcome_id = f"out:{site.id}:{arm.index}"
        label = self._outcome_labels.label(arm, verdict)
        self._acc.upsert(outcome_id, "outcome", lane, label, refs=[site.span])
        self._acc.set_owner(
            outcome_id, fqn, [f"{s}#{i}" for s, i in prefix] + [f"{site.id}#{arm.index}"]
        )
        self._acc.connect(node_id, outcome_id, "arm", label, site.id)


def _dedup(values: list[str]) -> list[str]:
    seen: dict[str, None] = {}
    for value in values:
        seen.setdefault(value, None)
    return list(seen)
