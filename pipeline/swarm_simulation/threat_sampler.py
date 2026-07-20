from __future__ import annotations

from dataclasses import asdict
from random import Random

from .swarm_config import SwarmConfig


def sample_trial_parameters(rng: Random, config: SwarmConfig) -> dict:
    return {
        "radar_scale": rng.uniform(config.radar_detection_scale_min, config.radar_detection_scale_max),
        "sam_kill_probability": rng.uniform(config.sam_kill_probability_min, config.sam_kill_probability_max),
        "ew_effectiveness": rng.uniform(config.ew_effectiveness_min, config.ew_effectiveness_max),
        "communication_loss": rng.uniform(config.communication_loss_min, config.communication_loss_max),
        "weather_severity": rng.uniform(config.weather_severity_min, config.weather_severity_max),
    }


def config_snapshot(config: SwarmConfig) -> dict:
    return asdict(config)
