from models.project_index import ProjectIndex


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
