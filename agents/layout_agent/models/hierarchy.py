from __future__ import annotations

from dataclasses import dataclass
from typing import Literal


@dataclass(frozen=True)
class HierarchyNode:
    path: str
    label: str
    kind: Literal["group", "service"]
    module_names: tuple[str, ...]
    children: tuple[HierarchyNode, ...]


@dataclass(frozen=True)
class HierarchyPlan:
    top: HierarchyNode
    service_modules: tuple[str, ...]
    architecture_modules: tuple[str, ...]
    orphans: tuple[str, ...]
