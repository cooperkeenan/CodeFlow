from collections.abc import Iterator

from tracer.models.index_records import ClassRecord, ProjectIndex
from tracer.services.analysis.syntax.types import normalize_type


class MroMethodFinder:
    def __init__(self, index: ProjectIndex) -> None:
        self._index = index

    def find_method(self, class_fqn: str, name: str) -> str | None:
        return self.find_project_method(class_fqn, name) or self.find_ext_fallback(class_fqn)

    def find_project_method(self, class_fqn: str, name: str) -> str | None:
        for record in self._mro(class_fqn):
            candidate = f"{record.fqn}.{name}"
            if candidate in self._index.functions:
                return candidate
        return None

    def find_ext_fallback(self, class_fqn: str) -> str | None:
        for record in self._mro(class_fqn):
            for base in record.bases:
                if base.startswith("ext:"):
                    return base
        return None

    def find_attr_type(self, class_fqn: str, attr: str) -> str | None:
        for record in self._mro(class_fqn):
            found = record.attr_types.get(attr)
            if found is not None:
                return normalize_type(found, self._index)
        return None

    def _mro(self, class_fqn: str) -> Iterator[ClassRecord]:
        seen: set[str] = set()
        stack = [class_fqn]
        while stack:
            current = stack.pop(0)
            if current in seen:
                continue
            seen.add(current)
            record = self._index.classes.get(current)
            if record is None:
                continue
            yield record
            stack.extend(base for base in record.bases if base not in seen)
