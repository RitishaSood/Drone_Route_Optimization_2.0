from __future__ import annotations

import numpy as np

from .drone_profile import get_drone_profile
from .environment_model import EnvironmentState, environment_from_dict
from .transition_model import TransitionWeights, evaluate_transition, normalize_node


class TransitionCostAdapter:
    def __init__(self, risk_lookup, drone_name, env, weights, xy_scale_km, z_scale_km):
        self.risk_lookup = risk_lookup
        self.drone = get_drone_profile(drone_name)
        self.env = environment_from_dict(env) if isinstance(env, dict) else (env or EnvironmentState())
        self.weights = weights or TransitionWeights()
        self.xy_scale_km = xy_scale_km
        self.z_scale_km = z_scale_km

    def risk_at(self, node) -> float:
        if self.risk_lookup is None:
            return 0.0
        node = normalize_node(node)
        if callable(self.risk_lookup):
            return float(self.risk_lookup(node))
        arr = np.asarray(self.risk_lookup)
        return float(arr[node["y"], node["x"]]) if arr.ndim == 2 else float(arr[node["z"], node["y"], node["x"]])

    def cost(self, previous_node, current_node, next_node, previous_speed_mps=None):
        metrics = evaluate_transition(previous_node, current_node, next_node, self.risk_at(next_node), self.drone, self.env, self.weights, previous_speed_mps, self.xy_scale_km, self.z_scale_km)
        return metrics.total_transition_cost, {
            "distance_km": metrics.distance_km,
            "time_seconds": metrics.time_seconds,
            "fuel_used": metrics.fuel_used,
            "wear_damage": metrics.wear_damage,
            "environment_penalty": metrics.environment_penalty,
            "acceleration_mps2": metrics.acceleration_mps2,
            "risk_cost": metrics.risk_cost,
            "feasible": metrics.feasible,
            "infeasible_reason": metrics.infeasible_reason,
        }
