from shared.models.diagram_template import DiagramTemplate

_MOD_W = 240
_MOD_GAP_X = 110
_NODE_W = 180
_NODE_GAP_X = 100


def place(template: DiagramTemplate) -> list[dict]:
    return [
        {
            "id": f"mod__{n.module_name}",
            "type": "moduleSummary",
            "position": {"x": i * (_MOD_W + _MOD_GAP_X), "y": 0},
            "data": {"label": n.label, "moduleName": n.module_name, "drillable": True},
        }
        for i, n in enumerate(template.nodes)
    ]


def place_component(template: DiagramTemplate) -> list[dict]:
    return [
        {
            "id": n.id,
            "type": "custom",
            "position": {"x": i * (_NODE_W + _NODE_GAP_X), "y": 0},
            "data": {
                "label": n.label, "module": n.module_name,
                "isEntry": n.style == "focus", "drillable": n.drillable, "tier": n.tier,
            },
        }
        for i, n in enumerate(template.nodes)
    ]
