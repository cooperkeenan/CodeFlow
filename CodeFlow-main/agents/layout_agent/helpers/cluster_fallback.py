from collections import OrderedDict

from shared.models.diagram_spec import Cluster, Component, Module, ZoneClusterPlan

DEFAULT_LABEL = "Components"


class ClusterFallback:
    def group_by_role(self, module: Module) -> list[ZoneClusterPlan]:
        plans: list[ZoneClusterPlan] = []
        for zone, components in module.zones.items():
            clusters = self._clusters(components)
            if clusters:
                plans.append(ZoneClusterPlan(zone=zone, clusters=clusters))
        return plans

    def _clusters(self, components: list[Component]) -> list[Cluster]:
        buckets: "OrderedDict[str, list[str]]" = OrderedDict()
        for component in components:
            if component.nested:
                continue
            label = self._label(component.role)
            buckets.setdefault(label, []).append(component.name)
        return [
            Cluster(label=label, style="grid", members=members)
            for label, members in buckets.items()
        ]

    def _label(self, role: str) -> str:
        if not role:
            return DEFAULT_LABEL
        return self._pluralise(role.replace("_", " ").title())

    def _pluralise(self, word: str) -> str:
        if word.endswith("y"):
            return f"{word[:-1]}ies"
        if word.endswith("s"):
            return word
        return f"{word}s"
