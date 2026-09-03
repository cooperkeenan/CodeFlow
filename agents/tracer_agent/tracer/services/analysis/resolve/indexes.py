from collections import defaultdict
from collections.abc import Mapping

from tracer.models.call_records import CallSite
from tracer.models.index_records import ProjectIndex


class ComponentIndex:
    def __init__(self, index: ProjectIndex) -> None:
        self._index = index

    def component_of(self, fqn: str) -> str | None:
        record = self._index.functions.get(fqn)
        if record is not None:
            return record.cls if record.cls is not None else record.module
        if fqn in self._index.classes:
            return fqn
        return None

    def is_project_target(self, fqn: str) -> bool:
        return fqn in self._index.functions or fqn in self._index.classes


class CallFqnLookup:
    def __init__(self, callsites: tuple[CallSite, ...]) -> None:
        by_key: dict[tuple[str, int, str], str] = {}
        for site in callsites:
            if not site.targets:
                continue
            fqn = site.targets[0].fqn
            key = (site.caller, site.line, site.call_source)
            existing = by_key.get(key)
            if existing is None or fqn < existing:
                by_key[key] = fqn
        self._by_key = by_key

    def fqn_for(self, caller: str, line: int, call_source: str) -> str:
        return self._by_key.get((caller, line, call_source), "")


class CallSiteCallerIndex:
    def __init__(self, callsites: tuple[CallSite, ...]) -> None:
        self._by_caller: dict[str, list[CallSite]] = defaultdict(list)
        for site in callsites:
            self._by_caller[site.caller].append(site)

    def callsites_for(self, caller_fqn: str) -> tuple[CallSite, ...]:
        return tuple(self._by_caller.get(caller_fqn, ()))


class CalleeIndex:
    def __init__(self, callsites: tuple[CallSite, ...]) -> None:
        self._by_caller: dict[str, set[str]] = {}
        for site in callsites:
            bucket = self._by_caller.setdefault(site.caller, set())
            for target in site.targets:
                bucket.add(target.fqn)

    def callees_of(self, fqn: str) -> tuple[str, ...]:
        return tuple(sorted(self._by_caller.get(fqn, ())))


class SccIndex:
    def __init__(self, component_of_node: Mapping[str, int], members: Mapping[int, frozenset[str]]) -> None:
        self._component_of_node = component_of_node
        self._members = members

    def scc_of(self, fqn: str) -> int | None:
        return self._component_of_node.get(fqn)

    def members_of(self, scc_id: int) -> frozenset[str]:
        return self._members.get(scc_id, frozenset())


class UniqueNameIndex:
    def __init__(self, index: ProjectIndex) -> None:
        by_name: dict[str, list[str]] = {}
        for record in index.functions.values():
            by_name.setdefault(record.name, []).append(record.fqn)
        self._unique = {name: fqns[0] for name, fqns in by_name.items() if len(fqns) == 1}

    def resolve(self, name: str) -> str | None:
        return self._unique.get(name)


class CallSiteArmIndex:
    def __init__(self, callsites: tuple[CallSite, ...]) -> None:
        self._by_arm: dict[tuple[str, int], list[CallSite]] = defaultdict(list)
        for site in callsites:
            for frame in site.context:
                self._by_arm[(frame.site_id, frame.arm_index)].append(site)

    def callsites_for(self, site_id: str, arm_index: int) -> tuple[CallSite, ...]:
        return tuple(self._by_arm.get((site_id, arm_index), ()))
