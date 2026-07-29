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
        return self._grouped(tuple(sorted(entries.values(), key=lambda e: e.id)))

    def _grouped(self, entries: tuple[FlowEntry, ...]) -> tuple[FlowEntry, ...]:
        by_router: dict[str, list[FlowEntry]] = {}
        for entry in entries:
            router = self._router_of(entry.handler_fqn)
            by_router.setdefault(router, []).append(entry)
        result: list[FlowEntry] = []
        for router, members in sorted(by_router.items()):
            if len(members) < 2:
                result.extend(members)
                continue
            result.append(self._group_entry(router, members))
        return tuple(sorted(result, key=lambda e: e.id))

    def _router_of(self, handler_fqn: str) -> str:
        record = self._index.functions.get(handler_fqn)
        return record.module if record is not None else handler_fqn

    def _group_entry(self, router: str, members: list[FlowEntry]) -> FlowEntry:
        head = members[0]
        short = router.rsplit(".", 1)[-1]
        return FlowEntry(
            id=f"entry:group:{router}",
            handler_fqn=head.handler_fqn,
            label=f"{short} · {len(members)} routes",
            service_root=head.service_root,
            members=tuple(m.handler_fqn for m in members),
            route_count=len(members),
        )

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
