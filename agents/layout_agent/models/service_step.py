from __future__ import annotations

from dataclasses import dataclass

from shared.models.diagram_template import DiagramType


@dataclass(frozen=True)
class ServiceStep:
    label: str
    description: str
    backing_components: tuple[str, ...]
    order_index: int


@dataclass(frozen=True)
class ServiceStepPlan:
    module_name: str
    purpose: str
    diagram_type: DiagramType
    steps: tuple[ServiceStep, ...]
