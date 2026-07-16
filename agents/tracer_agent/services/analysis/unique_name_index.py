from models.project_index import ProjectIndex


class UniqueNameIndex:
    def __init__(self, index: ProjectIndex) -> None:
        by_name: dict[str, list[str]] = {}
        for record in index.functions.values():
            by_name.setdefault(record.name, []).append(record.fqn)
        self._unique = {name: fqns[0] for name, fqns in by_name.items() if len(fqns) == 1}

    def resolve(self, name: str) -> str | None:
        return self._unique.get(name)
