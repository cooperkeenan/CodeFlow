from collections import defaultdict

from helpers.component_metrics import ComponentMetrics

from shared.models.diagram_spec import ComponentTier

DATA_ZONES = frozenset({"data", "domain", "models", "model", "schemas", "schema", "dto", "entities"})
PRIMARY_PER_ZONE = 6


class ImportanceScorer:
    def score(self, metric: ComponentMetrics) -> float:
        base = (
            3.0 * float(metric.is_entry)
            + 2.0 * metric.fan_out
            + 1.0 * metric.fan_in
            + 1.0 * metric.child_count
        )
        if metric.zone.lower() in DATA_ZONES and metric.fan_out == 0 and metric.child_count == 0:
            base *= 0.25
        return base

    def primary_tiers(
        self, metrics_by_name: dict[str, ComponentMetrics]
    ) -> dict[str, ComponentTier]:
        by_zone: dict[tuple[str, str], list[ComponentMetrics]] = defaultdict(list)
        for metric in metrics_by_name.values():
            by_zone[(metric.module, metric.zone)].append(metric)
        tiers: dict[str, ComponentTier] = {}
        for metrics in by_zone.values():
            ordered = sorted(metrics, key=lambda m: (-self.score(m), m.name))
            for index, metric in enumerate(ordered):
                primary = index < PRIMARY_PER_ZONE and self.score(metric) > 0
                tiers[metric.name] = "primary" if primary else "secondary"
        return tiers
