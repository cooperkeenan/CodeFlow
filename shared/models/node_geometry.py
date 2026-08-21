from dataclasses import dataclass


@dataclass(frozen=True)
class NodeGeometry:
    width: int
    height: int


NODE_GEOMETRY: dict[str, NodeGeometry] = {
    "pill": NodeGeometry(340, 152),
    "rect": NodeGeometry(340, 152),
    "decision": NodeGeometry(340, 160),
    "split_bar": NodeGeometry(290, 64),
    "effect": NodeGeometry(340, 152),
    "outcome": NodeGeometry(250, 104),
    "lane_header": NodeGeometry(260, 52),
    "pipeline": NodeGeometry(340, 126),
}


def geometry_for(shape: str) -> NodeGeometry:
    geometry = NODE_GEOMETRY.get(shape)
    if geometry is None:
        raise KeyError(f"no geometry registered for shape {shape!r}")
    return geometry


def geometry_payload() -> dict[str, dict[str, int]]:
    return {
        shape: {"width": geometry.width, "height": geometry.height}
        for shape, geometry in sorted(NODE_GEOMETRY.items())
    }
