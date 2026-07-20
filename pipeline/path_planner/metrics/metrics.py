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


def calculate_path_total_cost(
    cost_matrix: np.ndarray,
    path: List[Dict[str, int]],
) -> float:
    if not path:
        return 0.0

    total = 0.0
    for point in path:
        total += float(cost_matrix[point["y"], point["x"]])
    return float(total)


def calculate_path_cumulative_costs(
    cost_matrix: np.ndarray,
    path: List[Dict[str, int]],
) -> List[float]:
    cumulative = 0.0
    values: List[float] = []

    for point in path:
        cumulative += float(cost_matrix[point["y"], point["x"]])
        values.append(float(cumulative))

    return values


def calculate_path_step_count(path: List[Dict[str, int]]) -> int:
    return max(len(path) - 1, 0)


def calculate_fuel_metrics(
    total_distance_km: float,
    total_cost: float,
    turn_count: int,
    total_climb_z: float,
    drone_profile: DroneFuelProfile,
) -> Dict[str, object]:
    fuel_burn_per_km = getattr(drone_profile, "fuel_burn_per_km", getattr(drone_profile, "base_fuel_burn_per_km", 0.0))
    turn_fuel_penalty = getattr(drone_profile, "turn_fuel_penalty", getattr(drone_profile, "turn_fuel_factor", 0.0))
    climb_fuel_factor = getattr(drone_profile, "climb_fuel_factor", 0.0)
    threat_fuel_factor = getattr(drone_profile, "threat_fuel_factor", getattr(drone_profile, "weather_fuel_factor", 0.0))
    fuel_estimate = (
        total_distance_km * fuel_burn_per_km
        + total_cost * threat_fuel_factor
        + turn_count * turn_fuel_penalty
        + total_climb_z * climb_fuel_factor
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
    env=None,
    weights=None,
) -> Dict:
    path = result.get("path", [])

    total_distance_km = calculate_path_distance_km(path, cell_scale_km)
    turn_count = calculate_turn_count(path)
    step_count = calculate_path_step_count(path)
    search_efficiency = (len(path) / max(int(result.get("nodesVisited", 0)) or 1, 1)) if path else 0.0

    # Current project is 2.5D, so climb is zero for now.
    total_climb_z = 0.0

    cost_stats = calculate_path_cost_stats(cost_matrix, path)
    path_total_cost = calculate_path_total_cost(cost_matrix, path)

    fuel_metrics = calculate_fuel_metrics(
        total_distance_km=total_distance_km,
        total_cost=path_total_cost,
        turn_count=turn_count,
        total_climb_z=total_climb_z,
        drone_profile=drone_profile,
    )

    return {
        **result,
        "totalCost": float(path_total_cost if path else result.get("totalCost", 0.0)),
        "pathStepCount": int(step_count),
        "totalDistanceKm": float(total_distance_km),
        "totalClimbKm": 0.0,
        "totalDescentKm": float(total_climb_z),
        "turnCount": int(turn_count),
        "pathEfficiency": float(search_efficiency),
        "averageCost": cost_stats["averageCost"],
        "maxCellCost": cost_stats["maxCellCost"],
        "averageCellCost": cost_stats["averageCost"],
        "startNodeCost": float(cost_matrix[path[0]["y"], path[0]["x"]]) if path else 0.0,
        "goalNodeCost": float(cost_matrix[path[-1]["y"], path[-1]["x"]]) if path else 0.0,
        "meanCostPerTraversedNode": float(path_total_cost / len(path)) if path else 0.0,
        "meanCostPerStep": float(path_total_cost / step_count) if step_count > 0 else 0.0,
        **fuel_metrics,
        "droneName": drone_profile.name,
        "droneClass": drone_profile.uav_class,
        "propulsionClass": drone_profile.propulsion_class,
    }
