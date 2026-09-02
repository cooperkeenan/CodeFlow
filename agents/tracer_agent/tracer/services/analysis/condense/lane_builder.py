from tracer.models.sites import DispatchSite, FlowEntry
from tracer.models.verdicts import SignificanceResult
from tracer.services.analysis.indexing.service_root_resolver import ServiceRootResolver
from tracer.services.analysis.routes.label_synthesizer import LabelSynthesizer

from shared.models.flow_graph import Lane


class LaneBuilder:
    def __init__(self, roots: ServiceRootResolver, labels: LabelSynthesizer) -> None:
        self._roots = roots
        self._labels = labels

    def build(
        self,
        entries: tuple[FlowEntry, ...],
        dispatch_sites: tuple[DispatchSite, ...],
        significance: SignificanceResult,
    ) -> list[Lane]:
        entry_ids: dict[str, list[str]] = {}
        for entry in entries:
            entry_ids.setdefault(entry.service_root, []).append(entry.id)
        mass = self._mass(dispatch_sites, significance)
        lanes = [
            Lane(
                id=root,
                name=self._labels.humanize(root),
                entry_ids=sorted(ids),
                mass=round(mass.get(root, 0.0), 6),
            )
            for root, ids in entry_ids.items()
        ]
        return sorted(lanes, key=lambda lane: lane.id)

    def _mass(
        self, dispatch_sites: tuple[DispatchSite, ...], significance: SignificanceResult
    ) -> dict[str, float]:
        mass: dict[str, float] = {}
        for site_id, verdict in significance.verdicts.items():
            if verdict.verdict != "decision":
                continue
            owner = site_id.rsplit(":", 1)[0]
            root = self._roots.root_of(owner)
            mass[root] = mass.get(root, 0.0) + verdict.score
        for site in dispatch_sites:
            if site.kind == "route":
                root = self._roots.root_of(site.owner)
                mass[root] = mass.get(root, 0.0) + len(site.arms)
        return mass
