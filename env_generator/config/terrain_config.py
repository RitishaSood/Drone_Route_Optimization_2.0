from dataclasses import dataclass

@dataclass
class TerrainConfig:

    grid_size_x: int = 100
    grid_size_y: int = 100
    grid_size_z: int = 100

    cell_size_km: float = 1.0
    elevation_step_m: float = 100.0

    seed: int | None = None

    num_mountain_ranges: int = 4
    num_water_clusters: int = 5
    num_forest_clusters: int = 8

    mountain_height_min: int = 15
    mountain_height_max: int = 30

    hill_height_min: int = 8
    hill_height_max: int = 15

    plain_height_min: int = 3
    plain_height_max: int = 8

    valley_height_min: int = 1
    valley_height_max: int = 5