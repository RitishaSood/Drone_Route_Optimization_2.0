from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any

import numpy as np

from .drone_profile import get_drone_profile
from .environment_model import EnvironmentState, environment_from_dict
from .transition_model import TransitionWeights, evaluate_transition, normalize_node


@dataclass
class PathPerformanceSummary:
    drone_name: str
    drone_class: str
    propulsion_class: str
    node_count: int = 0
    transition_count: int = 0
    total_distance_km: float = 0.0
    total_climb_km: float = 0.0
    total_descent_km: float = 0.0
    total_time_seconds: float = 0.0
    total_time_minutes: float = 0.0
    average_speed_mps: float = 0.0
    total_fuel_used: float = 0.0
    fuel_capacity: float = 0.0
    fuel_remaining: float = 0.0
    fuel_feasible: bool = True
    total_wear_damage: float = 0.0
    health_capacity: float = 0.0
    health_remaining: float = 0.0
    health_feasible: bool = True
    max_turn_angle_deg: float = 0.0
    average_turn_angle_deg: float = 0.0
    total_environment_penalty: float = 0.0
    average_environment_penalty: float = 0.0
    environment_enabled: bool = False
    wind_enabled: bool = False
    rain_enabled: bool = False
    fog_enabled: bool = False
    snow_enabled: bool = False
    hail_enabled: bool = False
    turbulence_enabled: bool = False
    temperature_enabled: bool = False
    thunderstorm_enabled: bool = False
    wind_penalty: float = 0.0
    weather_penalty: float = 0.0
    turbulence_penalty: float = 0.0
    temperature_penalty: float = 0.0
    thunderstorm_penalty: float = 0.0
    total_ew_jamming_exposure: float = 0.0
    average_ew_jamming_exposure: float = 0.0
    max_ew_jamming_exposure: float = 0.0
    communication_loss_risk: float = 0.0
    gps_navigation_penalty: float = 0.0
    time_aware: bool = True
    mission_deadline_minutes: float = 120.0
    time_feasible: bool = True
    time_of_day_enabled: bool = False
    mission_start_hour: int = 6
    mission_duration_hours: float = 6.0
    time_sample_interval_minutes: int = 30
    day_night_mode_summary: str = "-"
    visual_time_multiplier_average: float = 1.0
    ir_time_multiplier_average: float = 1.0
    radar_time_multiplier_average: float = 1.0
    acoustic_time_multiplier_average: float = 1.0
    visual_weather_multiplier: float = 1.0
    ir_weather_multiplier: float = 1.0
    radar_weather_multiplier: float = 1.0
    acoustic_weather_multiplier: float = 1.0
    ew_jamming_enabled: bool = False
    infeasible_transition_count: int = 0
    infeasible_reasons: list[str] = field(default_factory=list)
    total_transition_cost: float = 0.0
    mission_feasible: bool = True
    metric_note: str = "Fuel, time, and wear values are simulation estimates for algorithm comparison, not certified real-world performance values."


def _environment_breakdown(env: EnvironmentState) -> dict[str, float]:
    if not getattr(env, "environment_enabled", False):
        return {
            "wind_penalty": 0.0,
            "weather_penalty": 0.0,
            "turbulence_penalty": 0.0,
            "temperature_penalty": 0.0,
            "thunderstorm_penalty": 0.0,
        }
    wind_penalty = (0.10 * env.wind_speed_mps + 0.08 * env.gust_speed_mps) if getattr(env, "wind_enabled", False) else 0.0
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
    if getattr(env, "temperature_enabled", False):
        if 0.0 <= env.temperature_c <= 40.0:
            temperature_penalty = 0.0
        elif env.temperature_c < 0.0:
            temperature_penalty = abs(env.temperature_c) * 0.2
        else:
            temperature_penalty = abs(env.temperature_c - 40.0) * 0.2
    else:
        temperature_penalty = 0.0
    thunderstorm_penalty = 50.0 if getattr(env, "thunderstorm_enabled", False) and env.thunderstorm else 0.0
    return {
        "wind_penalty": wind_penalty,
        "weather_penalty": weather_penalty,
        "turbulence_penalty": turbulence_penalty,
        "temperature_penalty": temperature_penalty,
        "thunderstorm_penalty": thunderstorm_penalty,
    }


def _risk_at(risk_lookup, node):
    if risk_lookup is None:
        return 0.0
    node = normalize_node(node)
    if callable(risk_lookup):
        return float(risk_lookup(node))
    arr = np.asarray(risk_lookup)
    if arr.ndim == 2:
        return float(arr[node["y"], node["x"]])
    return float(arr[node["z"], node["y"], node["x"]])


def summarize_path_performance(path, risk_lookup=None, drone_name: str | None = None, env: EnvironmentState | dict | None = None, weights: TransitionWeights | None = None, xy_scale_km: float = 1.0, z_scale_km: float = 0.1) -> PathPerformanceSummary:
    drone = get_drone_profile(drone_name)
    environment = environment_from_dict(env) if isinstance(env, dict) else (env or EnvironmentState())
    weights = weights or TransitionWeights()
    nodes = [normalize_node(node) for node in path or []]
    summary = PathPerformanceSummary(drone.name, drone.uav_class, drone.propulsion_class)
    summary.time_aware = getattr(environment, "time_aware", True)
    summary.mission_deadline_minutes = float(getattr(environment, "mission_deadline_minutes", 120.0) or 120.0)
    summary.ew_jamming_enabled = bool(getattr(environment, "ew_jamming_enabled", False))
    summary.environment_enabled = bool(getattr(environment, "environment_enabled", False))
    summary.wind_enabled = bool(getattr(environment, "wind_enabled", False))
    summary.rain_enabled = bool(getattr(environment, "rain_enabled", False))
    summary.fog_enabled = bool(getattr(environment, "fog_enabled", False))
    summary.snow_enabled = bool(getattr(environment, "snow_enabled", False))
    summary.hail_enabled = bool(getattr(environment, "hail_enabled", False))
    summary.turbulence_enabled = bool(getattr(environment, "turbulence_enabled", False))
    summary.temperature_enabled = bool(getattr(environment, "temperature_enabled", False))
    summary.thunderstorm_enabled = bool(getattr(environment, "thunderstorm_enabled", False))
    summary.time_of_day_enabled = bool(getattr(environment, "time_of_day_enabled", False))
    summary.mission_start_hour = int(getattr(environment, "mission_start_hour", 6) or 6)
    summary.mission_duration_hours = float(getattr(environment, "mission_duration_hours", 6.0) or 6.0)
    summary.time_sample_interval_minutes = int(getattr(environment, "time_sample_interval_minutes", 30) or 30)
    from .transition_model import calculate_time_multipliers
    tm = calculate_time_multipliers(environment)
    env_breakdown = _environment_breakdown(environment)
    summary.wind_penalty = env_breakdown["wind_penalty"]
    summary.weather_penalty = env_breakdown["weather_penalty"]
    summary.turbulence_penalty = env_breakdown["turbulence_penalty"]
    summary.temperature_penalty = env_breakdown["temperature_penalty"]
    summary.thunderstorm_penalty = env_breakdown["thunderstorm_penalty"]
    summary.day_night_mode_summary = tm["day_night_summary"]
    summary.visual_time_multiplier_average = tm["visual_time_multiplier"]
    summary.ir_time_multiplier_average = tm["ir_time_multiplier"]
    summary.radar_time_multiplier_average = tm["radar_time_multiplier"]
    summary.acoustic_time_multiplier_average = tm["acoustic_time_multiplier"]
    rain = environment.rain_intensity if getattr(environment, "rain_enabled", False) else 0.0
    fog = environment.fog_intensity if getattr(environment, "fog_enabled", False) else 0.0
    snow = environment.snow_intensity if getattr(environment, "snow_enabled", False) else 0.0
    wind = environment.wind_speed_mps if getattr(environment, "wind_enabled", False) else 0.0
    summary.visual_weather_multiplier = max(0.2, min(1.2, 1.0 - 0.30 * rain - 0.50 * fog - 0.25 * snow))
    summary.ir_weather_multiplier = max(0.4, min(1.2, 1.0 - 0.10 * rain - 0.15 * fog - 0.10 * snow))
    summary.radar_weather_multiplier = max(0.7, min(1.1, 1.0 - 0.05 * rain - 0.03 * snow))
    summary.acoustic_weather_multiplier = max(0.8, min(1.3, 1.0 + 0.10 * wind / 40.0 + 0.05 * rain))
    summary.node_count = len(nodes)
    summary.fuel_capacity = drone.fuel_capacity
    summary.health_capacity = drone.health_capacity
    prev_speed = drone.cruise_speed_mps
    prev_node = None
    prev_prev = None
    turn_angles = []
    for current, nxt in zip(nodes, nodes[1:]):
        risk = _risk_at(risk_lookup, nxt)
        metrics = evaluate_transition(prev_node, current, nxt, risk, drone, environment, weights, prev_speed, xy_scale_km, z_scale_km)
        summary.transition_count += 1
        summary.total_distance_km += metrics.distance_km
        summary.total_climb_km += metrics.climb_km
        summary.total_descent_km += metrics.descent_km
        summary.total_time_seconds += metrics.time_seconds
        summary.total_fuel_used += metrics.fuel_used
        summary.total_wear_damage += metrics.wear_damage
        summary.total_environment_penalty += metrics.environment_penalty
        summary.total_ew_jamming_exposure += metrics.ew_jamming_exposure
        summary.max_ew_jamming_exposure = max(summary.max_ew_jamming_exposure, metrics.ew_jamming_exposure)
        summary.communication_loss_risk = max(summary.communication_loss_risk, metrics.communication_loss_risk)
        summary.gps_navigation_penalty = max(summary.gps_navigation_penalty, metrics.gps_navigation_penalty)
        summary.total_transition_cost += metrics.total_transition_cost
        turn_angles.append(metrics.turn_angle_deg)
        summary.max_turn_angle_deg = max(summary.max_turn_angle_deg, metrics.turn_angle_deg)
        if not metrics.feasible:
            summary.infeasible_transition_count += 1
            if metrics.infeasible_reason:
                summary.infeasible_reasons.append(metrics.infeasible_reason)
        prev_prev = prev_node
        prev_node = current
        prev_speed = metrics.effective_speed_mps
    summary.total_time_minutes = summary.total_time_seconds / 60.0
    summary.average_speed_mps = summary.total_distance_km * 1000.0 / summary.total_time_seconds if summary.total_time_seconds > 0 else 0.0
    summary.average_environment_penalty = summary.total_environment_penalty / summary.transition_count if summary.transition_count > 0 else 0.0
    summary.average_ew_jamming_exposure = summary.total_ew_jamming_exposure / summary.transition_count if summary.transition_count > 0 else 0.0
    summary.fuel_remaining = summary.fuel_capacity - summary.total_fuel_used
    summary.fuel_feasible = summary.total_fuel_used <= summary.fuel_capacity
    summary.health_remaining = summary.health_capacity - summary.total_wear_damage
    summary.health_feasible = summary.health_remaining > 0
    summary.time_feasible = (not summary.time_aware) or (summary.total_time_minutes <= summary.mission_deadline_minutes)
    summary.mission_feasible = summary.fuel_feasible and summary.health_feasible and summary.time_feasible and summary.infeasible_transition_count == 0
    summary.average_turn_angle_deg = float(np.mean(turn_angles)) if turn_angles else 0.0
    return summary


def summary_to_dict(summary: PathPerformanceSummary) -> dict:
    return asdict(summary)
