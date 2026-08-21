from shared.models.node_geometry import NODE_GEOMETRY, NodeGeometry

TOUR_ONLY_GEOMETRY: dict[str, NodeGeometry] = {
    "card": NodeGeometry(900, 300),
    "snippet": NodeGeometry(620, 300),
}

TOUR_GEOMETRY: dict[str, NodeGeometry] = {**NODE_GEOMETRY, **TOUR_ONLY_GEOMETRY}


def tour_geometry_for(shape: str) -> NodeGeometry:
    geometry = TOUR_GEOMETRY.get(shape)
    if geometry is None:
        raise KeyError(f"no geometry registered for shape {shape!r}")
    return geometry


def tour_geometry_payload() -> dict[str, dict[str, int]]:
    return {
        shape: {"width": geometry.width, "height": geometry.height}
        for shape, geometry in sorted(TOUR_GEOMETRY.items())
    }
