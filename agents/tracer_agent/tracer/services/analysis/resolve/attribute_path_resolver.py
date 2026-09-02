from tracer.models.call_records import ResolvedTarget
from tracer.models.index_records import ProjectIndex
from tracer.services.analysis.resolve.mro_method_finder import MroMethodFinder


class AttributePathResolver:
    def __init__(self, index: ProjectIndex, mro: MroMethodFinder) -> None:
        self._index = index
        self._mro = mro

    def resolve(self, start: str, chain: list[str]) -> tuple[ResolvedTarget, ...] | None:
        if start.startswith("ext:"):
            return (ResolvedTarget(start, "resolved"),)
        if not chain:
            return None
        current = start
        for step in chain[:-1]:
            nxt = self._mro.find_attr_type(current, step)
            if nxt is None:
                return None
            if nxt.startswith("ext:"):
                return (ResolvedTarget(nxt, "resolved"),)
            current = nxt
        return self.resolve_method_fanout(current, chain[-1])

    def resolve_method_fanout(self, class_fqn: str, method_name: str) -> tuple[ResolvedTarget, ...] | None:
        own = self._mro.find_project_method(class_fqn, method_name)
        if own is not None:
            return (ResolvedTarget(own, "resolved"),)
        impls = self._index.implementations(class_fqn)
        if len(impls) == 1:
            target = self._mro.find_method(impls[0], method_name)
            return (ResolvedTarget(target, "resolved"),) if target else None
        if len(impls) >= 2:
            targets = tuple(
                ResolvedTarget(t, "resolved")
                for t in (self._mro.find_method(impl, method_name) for impl in sorted(impls))
                if t is not None
            )
            if targets:
                return targets
        ext_fallback = self._mro.find_ext_fallback(class_fqn)
        return (ResolvedTarget(ext_fallback, "resolved"),) if ext_fallback is not None else None
