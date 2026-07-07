from shared.models.repo_blueprint import RepoBlueprint


class ComponentPlacer:
    def dir_index(self, blueprint: RepoBlueprint) -> list[tuple[str, str, str]]:
        index = [
            (directory, module.root_path, zone.name)
            for module in blueprint.modules
            for zone in module.zones
            for directory in zone.directories
        ]
        index.sort(key=lambda t: len(t[0]), reverse=True)
        return index

    def place(self, file_path: str, index: list[tuple[str, str, str]]) -> tuple[str, str] | None:
        for directory, root, zone in index:
            if file_path.startswith(directory):
                return root, zone
        return None
