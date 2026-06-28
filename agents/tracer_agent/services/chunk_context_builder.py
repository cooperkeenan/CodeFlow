from shared.models.repo_blueprint import RepoBlueprint


class ChunkContextBuilder:
    def build(self, blueprint: RepoBlueprint, evidence: dict) -> str:
        parts: list[str] = []

        parts.append("MODULES")
        for module in blueprint.modules:
            zone_names = [z.name for z in module.zones]
            parts.append(f"{module.name} ({module.root_path}): zones {zone_names}")

        parts.append("")
        parts.append("HTTP CALLS")
        seen: set[tuple[str, str]] = set()
        for edge in evidence.get("http_edges", []):
            key = (edge.get("from", ""), edge.get("to", ""))
            if key not in seen:
                seen.add(key)
                parts.append(f"{key[0]} -> {key[1]}")

        return "\n".join(parts)
