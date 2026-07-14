from __future__ import annotations

from collections import defaultdict

from models.hierarchy import HierarchyNode
from shared.models.diagram_spec import DiagramSpec


class ModuleHierarchyBuilder:
    def build(self, spec: DiagramSpec) -> HierarchyNode:
        entries: list[tuple[str, list[str]]] = [
            (m.name, m.root_path.split("/"))
            for m in spec.modules
        ]
        return self._build_node("", "root", entries)

    def _build_node(
        self,
        path: str,
        label: str,
        modules: list[tuple[str, list[str]]],
    ) -> HierarchyNode:
        if not modules:
            return HierarchyNode(
                path=path, label=label, kind="group", module_names=(), children=()
            )

        if len(modules) == 1 and all(not parts for _, parts in modules):
            name = modules[0][0]
            return HierarchyNode(
                path=path, label=label, kind="service", module_names=(name,), children=()
            )

        grouped: dict[str, list[tuple[str, list[str]]]] = defaultdict(list)
        for mod_name, parts in modules:
            if parts:
                grouped[parts[0]].append((mod_name, parts[1:]))
            else:
                grouped[""].append((mod_name, []))

        children: list[HierarchyNode] = []
        for part, sub_modules in sorted(grouped.items()):
            child_path = f"{path}/{part}" if path else part
            child_label = part if part else label
            child = self._build_node(child_path, child_label, sub_modules)
            children.append(child)

        all_names = tuple(sorted(m for m, _ in modules))
        return HierarchyNode(
            path=path,
            label=label,
            kind="group",
            module_names=all_names,
            children=tuple(children),
        )
