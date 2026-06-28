import math

from shared.models.diagram_template import DiagramTemplate

_MOD_W = 240
_MOD_H = 110
_MOD_GAP_X = 110
_MOD_GAP_Y = 130
_NODE_W = 180
_NODE_H = 58
_NODE_GAP_X = 100
_NODE_GAP_Y = 80


def place(template: DiagramTemplate) -> list[dict]:
    n = len(template.nodes)
    cols = max(1, math.ceil(math.sqrt(n)))
    result = []
    for i, node in enumerate(template.nodes):
        result.append({
            "id": f"mod__{node.module_name}",
            "type": "moduleSummary",
            "position": {"x": (i % cols) * (_MOD_W + _MOD_GAP_X), "y": (i // cols) * (_MOD_H + _MOD_GAP_Y)},
            "data": {"label": node.label, "moduleName": node.module_name, "drillable": True},
        })
    return result


def place_component(template: DiagramTemplate) -> list[dict]:
    n = len(template.nodes)
    cols = max(1, math.ceil(math.sqrt(n)))
    result = []
    for i, node in enumerate(template.nodes):
        result.append({
            "id": node.id, "type": "custom",
            "position": {"x": (i % cols) * (_NODE_W + _NODE_GAP_X), "y": (i // cols) * (_NODE_H + _NODE_GAP_Y)},
            "data": {"label": node.label, "module": node.module_name, "isEntry": node.style == "focus", "drillable": node.drillable, "tier": node.tier},
        })
    return result
