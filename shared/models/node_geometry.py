from dataclasses import dataclass


@dataclass(frozen=True)
class NodeGeometry:
    width: int
    height: int


NODE_GEOMETRY: dict[str, NodeGeometry] = {
    "pill": NodeGeometry(280, 130),
    "rect": NodeGeometry(280, 130),
    "decision": NodeGeometry(280, 138),
    "split_bar": NodeGeometry(240, 56),
    "effect": NodeGeometry(280, 130),
    "outcome": NodeGeometry(200, 88),
    "lane_header": NodeGeometry(220, 44),
    "pipeline": NodeGeometry(280, 108),
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
