from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Any

from .drone_profile import DronePerformanceProfile
from .environment_model import EnvironmentState, clamp_environment


@dataclass
class TransitionWeights:
    risk_weight: float = 1.0
    distance_weight: float = 1.0
    fuel_weight: float = 1.0
    time_weight: float = 0.01
    wear_weight: float = 1.0
    environment_weight: float = 1.0
    acceleration_weight: float = 1.0
    ew_jamming_weight: float = 0.8


@dataclass
class TransitionMetrics:
    from_node: dict
    to_node: dict
    distance_km: float = 0.0
    climb_km: float = 0.0
    descent_km: float = 0.0
    turn_angle_deg: float = 0.0
    effective_speed_mps: float = 0.0
    time_seconds: float = 0.0
    fuel_used: float = 0.0
    wear_damage: float = 0.0
    environment_penalty: float = 0.0
    ew_jamming_exposure: float = 0.0
    communication_loss_risk: float = 0.0
    gps_navigation_penalty: float = 0.0
    acceleration_mps2: float = 0.0
    acceleration_cost: float = 0.0
    risk_cost: float = 0.0
    total_transition_cost: float = 0.0
    feasible: bool = True
    infeasible_reason: str | None = None


def normalize_node(node: Any) -> dict:
    if isinstance(node, dict):
        return {"x": int(node.get("x", 0)), "y": int(node.get("y", 0)), "z": int(node.get("z", 0))}
    if len(node) == 2:
        return {"x": int(node[0]), "y": int(node[1]), "z": 0}
    return {"x": int(node[0]), "y": int(node[1]), "z": int(node[2])}


def calculate_distance_km(a, b, xy_scale_km=1.0, z_scale_km=0.1):
    a = normalize_node(a)
    b = normalize_node(b)
    dx = (b["x"] - a["x"]) * xy_scale_km
    dy = (b["y"] - a["y"]) * xy_scale_km
    dz = (b["z"] - a["z"]) * z_scale_km
    return math.sqrt(dx * dx + dy * dy + dz * dz)


def calculate_climb_descent_km(a, b, z_scale_km=0.1):
    a = normalize_node(a)
    b = normalize_node(b)
    dz = (b["z"] - a["z"]) * z_scale_km
    return (max(dz, 0.0), max(-dz, 0.0))


def calculate_turn_angle_deg(prev_node, current_node, next_node):
    if prev_node is None:
        return 0.0
    a = normalize_node(prev_node)
    b = normalize_node(current_node)
    c = normalize_node(next_node)
    v1 = (b["x"] - a["x"], b["y"] - a["y"], b["z"] - a["z"])
    v2 = (c["x"] - b["x"], c["y"] - b["y"], c["z"] - b["z"])
    n1 = math.sqrt(sum(v * v for v in v1))
    n2 = math.sqrt(sum(v * v for v in v2))
    if n1 == 0 or n2 == 0:
        return 0.0
    dot = sum(x * y for x, y in zip(v1, v2)) / (n1 * n2)
    dot = max(-1.0, min(1.0, dot))
    return math.degrees(math.acos(dot))


def calculate_effective_speed_mps(drone, env, climb_km, distance_km):
    env = clamp_environment(env)
    wind = env.wind_speed_mps if getattr(env, "wind_enabled", False) and getattr(env, "environment_enabled", False) else 0.0
    rain = env.rain_intensity if getattr(env, "rain_enabled", False) and getattr(env, "environment_enabled", False) else 0.0
    turbulence = env.turbulence_intensity if getattr(env, "turbulence_enabled", False) and getattr(env, "environment_enabled", False) else 0.0
    speed = drone.cruise_speed_mps * (1.0 - 0.15 * wind / max(drone.max_wind_tolerance_mps, 1.0))
    if climb_km > 0:
        speed *= max(0.5, 1.0 - climb_km / max(distance_km, 1e-6) * 0.2)
    speed *= max(0.5, 1.0 - turbulence * 0.1 - rain * 0.05)
    return max(drone.min_speed_mps, min(drone.max_speed_mps, speed))


def calculate_time_seconds(distance_km, effective_speed_mps):
    if effective_speed_mps <= 0:
        return float("inf")
    return distance_km * 1000.0 / effective_speed_mps


def calculate_acceleration_mps2(prev_speed_mps, next_speed_mps, time_seconds):
    if time_seconds <= 0:
        return 0.0
    return (next_speed_mps - prev_speed_mps) / time_seconds


def calculate_environment_penalty(drone, env):
    env = clamp_environment(env)
    if not getattr(env, "environment_enabled", False):
        return 0.0
    wind_penalty = 0.0
    if getattr(env, "wind_enabled", False):
        wind_penalty = 0.10 * env.wind_speed_mps + 0.08 * env.gust_speed_mps
    if 0.0 <= env.temperature_c <= 40.0:
        temperature_penalty = 0.0
    elif env.temperature_c < 0.0:
        temperature_penalty = abs(env.temperature_c) * 0.2
    else:
        temperature_penalty = abs(env.temperature_c - 40.0) * 0.2
    weather_penalty = 0.0
    if getattr(env, "rain_enabled", False):
        weather_penalty += 5.0 * env.rain_intensity
    if getattr(env, "fog_enabled", False):
        weather_penalty += 4.0 * env.fog_intensity
    if getattr(env, "snow_enabled", False):
        weather_penalty += 4.0 * env.snow_intensity
    if getattr(env, "hail_enabled", False):
        weather_penalty += 8.0 * env.hail_intensity
    turbulence_penalty = 6.0 * env.turbulence_intensity if getattr(env, "turbulence_enabled", False) else 0.0
    temperature_penalty = temperature_penalty if getattr(env, "temperature_enabled", False) else 0.0
    thunderstorm_penalty = 50.0 if getattr(env, "thunderstorm_enabled", False) and env.thunderstorm else 0.0
    penalty = wind_penalty + weather_penalty + turbulence_penalty + temperature_penalty + thunderstorm_penalty
    return min(penalty, 100.0)

def _daylight_factor(hour):
    h = hour % 24
    if 6 <= h < 18:
        return 1.0
    if 5 <= h < 6 or 18 <= h < 19:
        return 0.5
    return 0.0

def calculate_time_multipliers(env):
    if not getattr(env, "time_of_day_enabled", False):
        return {
            "daylight_factor": 1.0,
            "visual_time_multiplier": 1.0,
            "ir_time_multiplier": 1.0,
            "radar_time_multiplier": 1.0,
            "acoustic_time_multiplier": 1.0,
            "ew_time_multiplier": 1.0,
            "day_night_summary": "Time-of-day effects disabled.",
        }
    daylight = _daylight_factor(getattr(env, "mission_start_hour", 6))
    if daylight == 0:
        ir = 1.15
        acoustic = 1.05
        summary = "night"
    elif daylight == 0.5:
        ir = 1.0
        acoustic = 1.0
        summary = "twilight"
    else:
        ir = 0.85
        acoustic = 1.0
        summary = "day"
    return {
        "daylight_factor": daylight,
        "visual_time_multiplier": 0.4 + 0.6 * daylight,
        "ir_time_multiplier": ir,
        "radar_time_multiplier": 1.0,
        "acoustic_time_multiplier": acoustic,
        "ew_time_multiplier": 1.0,
        "day_night_summary": summary,
    }


def calculate_ew_exposure(current_node, env):
    env = clamp_environment(env)
    if not getattr(env, "ew_jamming_enabled", False):
        return 0.0
    jammers = getattr(env, "ew_jammers", None) or []
    if not jammers:
        return 0.0
    cx = float(normalize_node(current_node)["x"])
    cy = float(normalize_node(current_node)["y"])
    cz = float(normalize_node(current_node)["z"])
    xy_scale_km = 1.0
    z_scale_km = 0.1
    exposures = []
    for jammer in jammers:
        sx = float(jammer.get("x", 0))
        sy = float(jammer.get("y", 0))
        sz = float(jammer.get("z", 0))
        strength = float(jammer.get("strength", 1.0) or 1.0)
        r0 = float(jammer.get("R0", jammer.get("max_range", 35.0)) or 35.0)
        dx = (cx - sx) * xy_scale_km
        dy = (cy - sy) * xy_scale_km
        dz = (cz - sz) * z_scale_km
        d = math.sqrt(dx * dx + dy * dy + dz * dz)
        if d > float(jammer.get("max_range", r0) or r0):
            p = 0.0
        else:
            p = strength / (1.0 + (d / max(r0, 1e-6)) ** 4)
        exposures.append(max(0.0, min(1.0, p)))
    if not exposures:
        return 0.0
    total = 1.0
    for exposure in exposures:
        total *= (1.0 - exposure)
    return max(0.0, min(1.0, 1.0 - total))


def calculate_fuel_used(drone, distance_km, climb_km, turn_angle_deg, acceleration_mps2, env, environment_penalty):
    env = clamp_environment(env)
    return (
        distance_km * drone.base_fuel_burn_per_km
        + climb_km * drone.climb_fuel_factor
        + (turn_angle_deg / 90.0) * drone.turn_fuel_factor
        + abs(acceleration_mps2) * drone.acceleration_fuel_factor
        + env.wind_speed_mps * drone.wind_fuel_factor
        + environment_penalty * drone.weather_fuel_factor
    )


def calculate_wear_damage(drone, distance_km, climb_km, turn_angle_deg, acceleration_mps2, env):
    env = clamp_environment(env)
    return (
        distance_km * drone.base_wear_per_km
        + climb_km * drone.climb_wear_factor
        + (turn_angle_deg / 90.0) * drone.turn_wear_factor
        + abs(acceleration_mps2) * drone.acceleration_wear_factor
        + env.turbulence_intensity * drone.turbulence_wear_factor
        + env.rain_intensity * drone.rain_wear_factor
        + env.hail_intensity * drone.hail_wear_factor
    )


def evaluate_transition(previous_node, current_node, next_node, risk_cost: float, drone: DronePerformanceProfile, env: EnvironmentState | None = None, weights: TransitionWeights | None = None, previous_speed_mps: float | None = None, xy_scale_km: float = 1.0, z_scale_km: float = 0.1) -> TransitionMetrics:
    env = clamp_environment(env or EnvironmentState())
    weights = weights or TransitionWeights()
    previous_speed_mps = drone.cruise_speed_mps if previous_speed_mps is None else previous_speed_mps
    current_node_n = normalize_node(current_node)
    next_node_n = normalize_node(next_node)
    prev_node_n = normalize_node(previous_node) if previous_node is not None else None
    distance_km = calculate_distance_km(current_node_n, next_node_n, xy_scale_km, z_scale_km)
    climb_km, descent_km = calculate_climb_descent_km(current_node_n, next_node_n, z_scale_km)
    turn_angle_deg = calculate_turn_angle_deg(prev_node_n, current_node_n, next_node_n)
    effective_speed = calculate_effective_speed_mps(drone, env, climb_km, distance_km)
    time_seconds = calculate_time_seconds(distance_km, effective_speed)
    acceleration = calculate_acceleration_mps2(previous_speed_mps, effective_speed, time_seconds)
    environment_penalty = calculate_environment_penalty(drone, env)
    ew_exposure = calculate_ew_exposure(next_node_n, env)
    fuel_used = calculate_fuel_used(drone, distance_km, climb_km, turn_angle_deg, acceleration, env, environment_penalty)
    wear_damage = calculate_wear_damage(drone, distance_km, climb_km, turn_angle_deg, acceleration, env)
    feasible = True
    reason = None
    if env.wind_speed_mps > drone.max_wind_tolerance_mps:
        feasible = False
        reason = "Wind exceeds tolerance"
    if env.time_aware and time_seconds > env.mission_deadline_minutes * 60.0:
        feasible = False
        reason = reason or "Mission deadline exceeded"
    communication_loss_risk = min(1.0, ew_exposure * 0.7)
    gps_navigation_penalty = min(1.0, ew_exposure * 0.6)
    total_cost = (
        weights.risk_weight * risk_cost
        + weights.distance_weight * distance_km
        + weights.fuel_weight * fuel_used
        + weights.time_weight * time_seconds
        + weights.wear_weight * wear_damage
        + weights.environment_weight * environment_penalty
        + weights.ew_jamming_weight * ew_exposure
        + weights.acceleration_weight * abs(acceleration)
    )
    return TransitionMetrics(
        current_node_n,
        next_node_n,
        distance_km,
        climb_km,
        descent_km,
        turn_angle_deg,
        effective_speed,
        time_seconds,
        fuel_used,
        wear_damage,
        environment_penalty,
        ew_exposure,
        communication_loss_risk,
        gps_navigation_penalty,
        acceleration,
        abs(acceleration),
        risk_cost,
        total_cost,
        feasible,
        reason,
    )
