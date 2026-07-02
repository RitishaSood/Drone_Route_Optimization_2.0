import math
from typing import Dict, List

import numpy as np

from pipeline.path_planner.drone_profiles import DroneFuelProfile


def calculate_path_distance_km(path: List[Dict[str, int]], cell_scale_km: float = 1.0) -> float:
    if len(path) < 2:
        return 0.0

    distance = 0.0

    for prev, curr in zip(path, path[1:]):
        dx = curr["x"] - prev["x"]
        dy = curr["y"] - prev["y"]
        distance += math.sqrt(dx * dx + dy * dy) * cell_scale_km

    return distance


def calculate_turn_count(path: List[Dict[str, int]]) -> int:
    if len(path) < 3:
        return 0

    turns = 0

    prev_direction = None

    for a, b in zip(path, path[1:]):
        direction = (
            b["x"] - a["x"],
            b["y"] - a["y"],
        )

        if prev_direction is not None and direction != prev_direction:
            turns += 1

        prev_direction = direction

    return turns


def calculate_path_cost_stats(
    cost_matrix: np.ndarray,
    path: List[Dict[str, int]],
) -> Dict[str, float]:
    if not path:
        return {
            "averageCost": 0.0,
            "maxCellCost": 0.0,
        }

    values = []

    for point in path:
        x = point["x"]
        y = point["y"]
        values.append(float(cost_matrix[y, x]))

    return {
        "averageCost": float(np.mean(values)),
        "maxCellCost": float(np.max(values)),
    }


def calculate_fuel_metrics(
    total_distance_km: float,
    total_cost: float,
    turn_count: int,
    total_climb_z: float,
    drone_profile: DroneFuelProfile,
) -> Dict[str, object]:
    fuel_estimate = (
        total_distance_km * drone_profile.fuel_burn_per_km
        + total_cost * drone_profile.threat_fuel_factor
        + turn_count * drone_profile.turn_fuel_penalty
        + total_climb_z * drone_profile.climb_fuel_factor
    )

    fuel_remaining = drone_profile.fuel_capacity - fuel_estimate

    return {
        "fuelEstimate": float(fuel_estimate),
        "fuelCapacity": float(drone_profile.fuel_capacity),
        "fuelRemaining": float(fuel_remaining),
        "fuelFeasible": fuel_estimate <= drone_profile.fuel_capacity,
        "fuelUnit": "model_units",
    }


def enrich_algorithm_result(
    result: Dict,
    cost_matrix: np.ndarray,
    drone_profile: DroneFuelProfile,
    cell_scale_km: float = 1.0,
) -> Dict:
    path = result.get("path", [])

    total_distance_km = calculate_path_distance_km(path, cell_scale_km)
    turn_count = calculate_turn_count(path)

    # Current project is 2.5D, so climb is zero for now.
    total_climb_z = 0.0

    cost_stats = calculate_path_cost_stats(cost_matrix, path)

    fuel_metrics = calculate_fuel_metrics(
        total_distance_km=total_distance_km,
        total_cost=float(result.get("totalCost", 0.0)),
        turn_count=turn_count,
        total_climb_z=total_climb_z,
        drone_profile=drone_profile,
    )

    return {
        **result,
        "totalDistanceKm": float(total_distance_km),
        "turnCount": int(turn_count),
        "averageCost": cost_stats["averageCost"],
        "maxCellCost": cost_stats["maxCellCost"],
        **fuel_metrics,
        "droneName": drone_profile.name,
        "droneClass": drone_profile.uav_class,
        "propulsionClass": drone_profile.propulsion_class,
    }