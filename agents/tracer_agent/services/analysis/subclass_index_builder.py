from collections.abc import Sequence

from services.analysis.class_analysis import ClassAnalysis


class SubclassIndexBuilder:
    def build(self, analyses: Sequence[ClassAnalysis]) -> dict[str, tuple[str, ...]]:
        by_fqn = {a.record.fqn: a for a in analyses}
        children: dict[str, list[str]] = {}
        for analysis in analyses:
            for base in analysis.record.bases:
                if base in by_fqn:
                    children.setdefault(base, []).append(analysis.record.fqn)
        result: dict[str, tuple[str, ...]] = {}
        for fqn in by_fqn:
            result[fqn] = tuple(sorted(self._transitive_concrete(fqn, children, by_fqn)))
        return result

    def _transitive_concrete(
        self, fqn: str, children: dict[str, list[str]], by_fqn: dict[str, ClassAnalysis]
    ) -> set[str]:
        found: set[str] = set()
        seen: set[str] = set()
        stack = list(children.get(fqn, []))
        while stack:
            child = stack.pop()
            if child in seen:
                continue
            seen.add(child)
            if not by_fqn[child].is_abstract:
                found.add(child)
            stack.extend(children.get(child, []))
        return found
