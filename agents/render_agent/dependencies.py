from placement.registry import PlacementRegistry
from services.placement_service import PlacementService


def get_placement_service() -> PlacementService:
    return PlacementService(PlacementRegistry())
