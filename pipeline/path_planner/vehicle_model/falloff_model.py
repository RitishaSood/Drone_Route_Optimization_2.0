from __future__ import annotations

from dataclasses import dataclass
import math


@dataclass
class FalloffConfig:
    falloff_model: str = "soft_inverse_power"
    R0: float = 35.0
    max_range: float = 60.0
    falloff_power: float = 2.5
    decay_k: float = 35.0
    sigma: float = 30.0
    floor_probability: float = 0.02
    max_probability: float = 1.0
    use_hard_range_cutoff: bool = False
    coverage_threshold: float = 0.15


def clamp(value: float, min_value: float, max_value: float) -> float:
    return max(min_value, min(max_value, value))


def compute_falloff_probability(distance_km: float, config: FalloffConfig) -> float:
    if config.use_hard_range_cutoff and distance_km > config.max_range:
        return 0.0
    p_floor = clamp(config.floor_probability, 0.0, 1.0)
    p_max = clamp(config.max_probability, 0.0, 1.0)
    if config.falloff_model == "exponential":
        value = p_floor + (p_max - p_floor) * math.exp(-distance_km / max(config.decay_k, 1e-9))
    elif config.falloff_model == "gaussian":
        value = p_floor + (p_max - p_floor) * math.exp(-0.5 * (distance_km / max(config.sigma, 1e-9)) ** 2)
    else:
        value = p_floor + (p_max - p_floor) / (1.0 + (distance_km / max(config.R0, 1e-9)) ** config.falloff_power)
    return clamp(value, 0.0, 1.0)
