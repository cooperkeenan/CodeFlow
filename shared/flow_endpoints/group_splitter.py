from dataclasses import replace
from math import ceil

from shared.flow_endpoints.endpoint_group import EndpointGroup, GroupRoute
from shared.flow_endpoints.route_segments import literal_segments

_INDEX = ""
_INDEX_TEXT = "index"


class GroupSplitter:
    def __init__(self, max_routes: int = 8, min_routes: int = 3) -> None:
        self._max = max_routes
        self._min = min_routes

    def split(
        self,
        group_id: str,
        name: str,
        entry_id: str,
        routes: list[GroupRoute] | tuple[GroupRoute, ...],
        depth: int,
    ) -> list[EndpointGroup]:
        ordered = tuple(sorted(routes, key=lambda r: (r.path, r.method, r.handler_fqn)))
        if len(ordered) <= self._max:
            return [self._group(group_id, name, None, entry_id, ordered, (), False)]
        buckets = self._bucket(ordered, depth)
        keys = sorted(buckets)
        if len(keys) == 1:
            if keys[0] != _INDEX:
                return self.split(group_id, name, entry_id, ordered, depth + 1)
            return [self._group(group_id, name, None, entry_id, ordered, (), True)]
        big = [k for k in keys if k != _INDEX and len(buckets[k]) >= self._min]
        small = [k for k in keys if k not in big]
        chunks = self._chunks(group_id, name, entry_id, small, buckets)
        if not big and len(chunks) == 1:
            return [self._group(group_id, name, None, entry_id, ordered, (), True)]
        subtrees = [
            self._child(self.split(f"{group_id}/{k}", k, entry_id, buckets[k], depth + 1), group_id)
            for k in big
        ]
        children = sorted([s[0] for s in subtrees] + chunks, key=lambda g: g.id)
        by_id = {s[0].id: s for s in subtrees}
        out = [self._group(group_id, name, None, entry_id, ordered, tuple(c.id for c in children), False)]
        for child in children:
            out.extend(by_id.get(child.id, [child]))
        return out

    def _bucket(
        self, routes: tuple[GroupRoute, ...], depth: int
    ) -> dict[str, list[GroupRoute]]:
        buckets: dict[str, list[GroupRoute]] = {}
        for route in routes:
            segments = literal_segments(route.path)
            key = segments[depth] if depth < len(segments) else _INDEX
            buckets.setdefault(key, []).append(route)
        return buckets

    def _chunks(
        self,
        group_id: str,
        name: str,
        entry_id: str,
        keys: list[str],
        buckets: dict[str, list[GroupRoute]],
    ) -> list[EndpointGroup]:
        if not keys:
            return []
        total = sum(len(buckets[k]) for k in keys)
        target = ceil(total / ceil(total / self._max))
        packed: list[list[str]] = [[]]
        size = 0
        for key in keys:
            count = len(buckets[key])
            if packed[-1] and (size >= target or size + count > self._max):
                packed.append([])
                size = 0
            packed[-1].append(key)
            size += count
        return [self._chunk(group_id, name, entry_id, p, buckets, len(packed) == 1) for p in packed]

    def _chunk(
        self,
        group_id: str,
        name: str,
        entry_id: str,
        keys: list[str],
        buckets: dict[str, list[GroupRoute]],
        only: bool,
    ) -> EndpointGroup:
        routes = tuple(r for k in keys for r in buckets[k])
        first, last = (k or _INDEX_TEXT for k in (keys[0], keys[-1]))
        label = "other" if only else f"{first}…{last}"
        return self._group(
            f"{group_id}/~{first}", f"{name} — {label}", group_id, entry_id,
            tuple(sorted(routes, key=lambda r: (r.path, r.method, r.handler_fqn))),
            (), len(routes) > self._max,
        )

    def _child(self, groups: list[EndpointGroup], parent_id: str) -> list[EndpointGroup]:
        return [replace(groups[0], parent_id=parent_id), *groups[1:]]

    def _group(
        self,
        group_id: str,
        name: str,
        parent_id: str | None,
        entry_id: str,
        routes: tuple[GroupRoute, ...],
        children: tuple[str, ...],
        overflow: bool,
    ) -> EndpointGroup:
        return EndpointGroup(group_id, name, parent_id, entry_id, routes, children, overflow)
