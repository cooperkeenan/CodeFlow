class RawMerger:
    def merge(self, raws: list[dict]) -> dict:
        components: list[dict] = []
        edges: list[dict] = []
        external_actors: list[dict] = []
        entry_points: list[str] = []

        seen_components: set[str] = set()
        seen_edges: set[tuple[str, str, str]] = set()
        seen_actors: set[str] = set()
        seen_entry_points: set[str] = set()

        for raw in raws:
            for comp in raw.get("components", []):
                if not isinstance(comp, dict):
                    continue
                name = comp.get("name")
                if not name or name in seen_components:
                    continue
                seen_components.add(name)
                components.append(comp)

            for edge in raw.get("edges", []):
                if not isinstance(edge, dict):
                    continue
                key = (
                    edge.get("source", ""),
                    edge.get("target", ""),
                    edge.get("edge_type", ""),
                )
                if key in seen_edges:
                    continue
                seen_edges.add(key)
                edges.append(edge)

            for actor in raw.get("external_actors", []):
                if not isinstance(actor, dict):
                    continue
                name = actor.get("name")
                if not name or name in seen_actors:
                    continue
                seen_actors.add(name)
                external_actors.append(actor)

            for ep in raw.get("entry_points", []):
                if ep not in seen_entry_points:
                    seen_entry_points.add(ep)
                    entry_points.append(ep)

        return {
            "components": components,
            "edges": edges,
            "external_actors": external_actors,
            "entry_points": entry_points,
        }
