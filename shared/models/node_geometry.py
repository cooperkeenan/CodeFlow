from dataclasses import dataclass


@dataclass(frozen=True)
class NodeGeometry:
    width: int
    height: int


NODE_GEOMETRY: dict[str, NodeGeometry] = {
    "pill": NodeGeometry(220, 60),
    "rect": NodeGeometry(180, 60),
    "decision": NodeGeometry(200, 68),
    "split_bar": NodeGeometry(200, 40),
    "effect": NodeGeometry(184, 60),
    "outcome": NodeGeometry(160, 52),
    "lane_header": NodeGeometry(220, 44),
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
