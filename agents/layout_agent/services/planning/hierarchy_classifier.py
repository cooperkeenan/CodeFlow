from __future__ import annotations

from core.hierarchy_config import HierarchyConfig
from helpers.connected_components import ConnectedComponents
from helpers.hierarchy_tree import ModuleHierarchyBuilder
from models.hierarchy import HierarchyNode, HierarchyPlan
from shared.models.diagram_spec import DiagramSpec, Module


class HierarchyClassifier:
    def __init__(
        self,
        tree_builder: ModuleHierarchyBuilder,
        connected: ConnectedComponents,
        config: HierarchyConfig,
    ) -> None:
        self._tree_builder = tree_builder
        self._connected = connected
        self._config = config

    def classify(self, spec: DiagramSpec) -> HierarchyPlan:
        tree = self._tree_builder.build(spec)
        collapsed = self._collapse(tree)
        module_map = {m.name: m for m in spec.modules}
        all_names: set[str] = set(module_map)
        service_names = {m.name for m in spec.modules if m.is_service}
        if service_names:
            return self._classify_by_service(collapsed, all_names, service_names)
        return self._classify_by_connectivity(spec, collapsed, module_map, all_names)

    def _classify_by_service(
        self,
        collapsed: HierarchyNode,
        all_names: set[str],
        service_names: set[str],
    ) -> HierarchyPlan:
        architecture_modules = tuple(sorted(service_names))
        service_modules = tuple(sorted(service_names))
        orphans = tuple(sorted(all_names - service_names))
        return HierarchyPlan(
            top=collapsed,
            service_modules=service_modules,
            architecture_modules=architecture_modules,
            orphans=orphans,
        )

    def _classify_by_connectivity(
        self,
        spec: DiagramSpec,
        collapsed: HierarchyNode,
        module_map: dict[str, Module],
        all_names: set[str],
    ) -> HierarchyPlan:
        connected = self._connected.largest(spec)
        orphans = tuple(sorted(all_names - connected))
        effective = self._effective_group(collapsed, connected)
        if effective is None:
            architecture_modules: tuple[str, ...] = ()
        else:
            architecture_modules = tuple(
                sorted(n for n in effective.module_names if n in connected)
            )
        leaf_names = self._leaf_module_names(collapsed)
        service_modules = tuple(
            sorted(
                n for n in all_names
                if n in leaf_names
                or self._comp_count(n, module_map) <= self._config.service_max_components
            )
        )
        return HierarchyPlan(
            top=collapsed,
            service_modules=service_modules,
            architecture_modules=architecture_modules,
            orphans=orphans,
        )

    def _collapse(self, node: HierarchyNode) -> HierarchyNode:
        if node.kind == "service":
            return node
        collapsed_children = tuple(self._collapse(c) for c in node.children)
        if len(collapsed_children) == 1:
            return collapsed_children[0]
        return HierarchyNode(
            path=node.path,
            label=node.label,
            kind=node.kind,
            module_names=node.module_names,
            children=collapsed_children,
        )

    def _effective_group(
        self, node: HierarchyNode, connected: set[str]
    ) -> HierarchyNode | None:
        if node.kind == "service":
            return None
        for child in node.children:
            deeper = self._effective_group(child, connected)
            if deeper is not None:
                return deeper
        connected_child_count = sum(
            1 for c in node.children if any(n in connected for n in c.module_names)
        )
        if connected_child_count >= self._config.min_group_children:
            return node
        return None

    def _leaf_module_names(self, node: HierarchyNode) -> set[str]:
        if node.kind == "service":
            return set(node.module_names)
        result: set[str] = set()
        for child in node.children:
            result |= self._leaf_module_names(child)
        return result

    def _comp_count(self, name: str, module_map: dict[str, Module]) -> int:
        module = module_map.get(name)
        if module is None:
            return 0
        return sum(len(comps) for comps in module.zones.values())
