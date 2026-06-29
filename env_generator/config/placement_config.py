from dataclasses import dataclass

@dataclass
class PlacementConfig:
    radar_separation: int = 18
    visual_separation: int = 14
    infrared_separation: int = 14
    acoustic_separation: int = 14

    coverage_weight: float = 0.5
    suitability_weight: float = 0.5

    allow_water: bool = False

    radar_marker = "^"
    infrared_marker = "s"
    acoustic_marker = "o"
    visual_marker = "D"