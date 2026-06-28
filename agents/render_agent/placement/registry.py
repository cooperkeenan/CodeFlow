from typing import Callable

from placement.container import place_component_container as _place_container
from placement.dependency_graph import place as _place_dependency_graph
from placement.hierarchy import place as _place_hierarchy
from placement.hierarchy import place_component as _place_hierarchy_component
from placement.hub_and_spoke import place as _place_hub_and_spoke
from placement.hub_and_spoke import place_component as _place_hub_and_spoke_component
from placement.layered_tier import place as _place_layered_tier
from placement.mesh import place as _place_mesh
from placement.module_view import place as _place_module_view
from placement.neighborhood import place_component as _place_neighborhood_component
from placement.pipeline import place as _place_pipeline
from placement.relationship import place as _place_relationship
from shared.models.diagram_template import DiagramTemplate, DiagramType

PlacementFn = Callable[[DiagramTemplate], list[dict]]

_FNS: dict[str, PlacementFn] = {
    "pipeline": _place_pipeline,
    "hub_and_spoke": _place_hub_and_spoke,
    "layered_tier": _place_layered_tier,
    "hierarchy": _place_hierarchy,
    "mesh": _place_mesh,
    "dependency_graph": _place_dependency_graph,
    "relationship": _place_relationship,
    "module": _place_module_view,
    "zoned": _place_module_view,
    "component_pipeline": _place_neighborhood_component,
    "component_hub_and_spoke": _place_hub_and_spoke_component,
    "component_layered_tier": _place_neighborhood_component,
    "component_hierarchy": _place_hierarchy_component,
    "component_mesh": _place_neighborhood_component,
    "component_dependency_graph": _place_neighborhood_component,
    "component_relationship": _place_neighborhood_component,
    "component_container": _place_container,
}


class PlacementRegistry:
    def get(self, diagram_type: DiagramType) -> PlacementFn:
        return _FNS.get(diagram_type, _FNS["dependency_graph"])
