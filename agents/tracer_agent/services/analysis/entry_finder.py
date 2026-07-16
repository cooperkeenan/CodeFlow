from models.arm import Arm
from models.dispatch_site import DispatchSite
from models.flow_entry import FlowEntry
from models.project_index import ProjectIndex
from services.analysis.label_synthesizer import LabelSynthesizer
from services.analysis.route_handler_locator import RouteHandlerLocator
from services.analysis.service_root_resolver import ServiceRootResolver


class EntryFinder:
    def __init__(
        self,
        index: ProjectIndex,
        locator: RouteHandlerLocator,
        roots: ServiceRootResolver,
        labels: LabelSynthesizer,
    ) -> None:
        self._index = index
        self._locator = locator
        self._roots = roots
        self._labels = labels

    def find(self, dispatch_sites: tuple[DispatchSite, ...]) -> tuple[FlowEntry, ...]:
        entries: dict[str, FlowEntry] = {}
        for site in dispatch_sites:
            if site.kind != "route":
                continue
            for arm in site.arms:
                entry = self._route_entry(site, arm)
                if entry is not None:
                    entries.setdefault(entry.id, entry)
        return tuple(sorted(entries.values(), key=lambda e: e.id))

    def _route_entry(self, site: DispatchSite, arm: Arm) -> FlowEntry | None:
        method, _, path = arm.label_source.partition(" ")
        handler = self._handler_fqn(site, arm, method, path)
        if handler is None:
            return None
        return FlowEntry(
            id=f"entry:{handler}",
            handler_fqn=handler,
            label=arm.label_source,
            service_root=self._roots.root_of(handler),
            method=method,
            path=path,
        )

    def _handler_fqn(self, site: DispatchSite, arm: Arm, method: str, path: str) -> str | None:
        if arm.callsites:
            return arm.callsites[0].caller
        located = self._locator.locate(site.owner, method.lower(), path)
        if located is not None and located in self._index.functions:
            return located
        return None
