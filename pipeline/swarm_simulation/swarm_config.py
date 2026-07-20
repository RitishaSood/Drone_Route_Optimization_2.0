from __future__ import annotations

from dataclasses import dataclass, field, asdict


DEFAULT_STRATEGIES = [
    "single_route",
    "split_routes",
    "decoy_lead",
    "distributed_routing",
]


@dataclass
class SwarmConfig:
    swarm_enabled: bool = True
    swarm_sizes: list[int] = field(default_factory=lambda: [1, 2, 4, 8, 16])
    num_monte_carlo_trials: int = 1000
    strategies: list[str] = field(default_factory=lambda: list(DEFAULT_STRATEGIES))
    required_survivors: int = 1
    target_coverage_threshold: float = 0.7
    decoy_fraction: float = 0.25
    radar_detection_scale_min: float = 0.8
    radar_detection_scale_max: float = 1.2
    sam_kill_probability_min: float = 0.3
    sam_kill_probability_max: float = 0.8
    ew_effectiveness_min: float = 0.2
    ew_effectiveness_max: float = 0.9
    communication_loss_min: float = 0.05
    communication_loss_max: float = 0.4
    weather_severity_min: float = 0.0
    weather_severity_max: float = 1.0
    lost_drone_penalty: float = 100.0
    communication_penalty: float = 10.0
    weather_penalty: float = 20.0
    decoy_penalty: float = 25.0
    decoy_saturation_effect: float = 0.25


def _clamp(value: float, low: float, high: float) -> float:
    return max(low, min(high, value))


def normalize_swarm_config(data: dict | None) -> SwarmConfig:
    raw = data or {}
    cfg = SwarmConfig()
    swarm_sizes = []
    for size in raw.get("swarmSizes", cfg.swarm_sizes):
        try:
            value = int(size)
        except (TypeError, ValueError):
            continue
        if value > 0:
            swarm_sizes.append(value)
    cfg.swarm_sizes = swarm_sizes or list(SwarmConfig().swarm_sizes)
    cfg.swarm_enabled = bool(raw.get("swarmEnabled", cfg.swarm_enabled))
    cfg.num_monte_carlo_trials = max(1, int(raw.get("numMonteCarloTrials", cfg.num_monte_carlo_trials) or cfg.num_monte_carlo_trials))
    strategies = [s for s in raw.get("strategies", cfg.strategies) if s in DEFAULT_STRATEGIES]
    cfg.strategies = strategies or list(DEFAULT_STRATEGIES)
    cfg.required_survivors = max(1, int(raw.get("requiredSurvivors", cfg.required_survivors) or cfg.required_survivors))
    cfg.target_coverage_threshold = _clamp(float(raw.get("targetCoverageThreshold", cfg.target_coverage_threshold) or cfg.target_coverage_threshold), 0.0, 1.0)
    cfg.decoy_fraction = _clamp(float(raw.get("decoyFraction", cfg.decoy_fraction) or cfg.decoy_fraction), 0.0, 1.0)
    cfg.radar_detection_scale_min = _clamp(float(raw.get("radarDetectionScaleMin", cfg.radar_detection_scale_min) or cfg.radar_detection_scale_min), 0.0, 1.0)
    cfg.radar_detection_scale_max = max(cfg.radar_detection_scale_min, _clamp(float(raw.get("radarDetectionScaleMax", cfg.radar_detection_scale_max) or cfg.radar_detection_scale_max), 0.0, 2.0))
    cfg.sam_kill_probability_min = _clamp(float(raw.get("samKillProbabilityMin", cfg.sam_kill_probability_min) or cfg.sam_kill_probability_min), 0.0, 1.0)
    cfg.sam_kill_probability_max = max(cfg.sam_kill_probability_min, _clamp(float(raw.get("samKillProbabilityMax", cfg.sam_kill_probability_max) or cfg.sam_kill_probability_max), 0.0, 1.0))
    cfg.ew_effectiveness_min = _clamp(float(raw.get("ewEffectivenessMin", cfg.ew_effectiveness_min) or cfg.ew_effectiveness_min), 0.0, 1.0)
    cfg.ew_effectiveness_max = max(cfg.ew_effectiveness_min, _clamp(float(raw.get("ewEffectivenessMax", cfg.ew_effectiveness_max) or cfg.ew_effectiveness_max), 0.0, 1.0))
    cfg.communication_loss_min = _clamp(float(raw.get("communicationLossMin", cfg.communication_loss_min) or cfg.communication_loss_min), 0.0, 1.0)
    cfg.communication_loss_max = max(cfg.communication_loss_min, _clamp(float(raw.get("communicationLossMax", cfg.communication_loss_max) or cfg.communication_loss_max), 0.0, 1.0))
    cfg.weather_severity_min = _clamp(float(raw.get("weatherSeverityMin", cfg.weather_severity_min) or cfg.weather_severity_min), 0.0, 1.0)
    cfg.weather_severity_max = max(cfg.weather_severity_min, _clamp(float(raw.get("weatherSeverityMax", cfg.weather_severity_max) or cfg.weather_severity_max), 0.0, 1.0))
    cfg.lost_drone_penalty = max(0.0, float(raw.get("lostDronePenalty", cfg.lost_drone_penalty) or cfg.lost_drone_penalty))
    cfg.communication_penalty = max(0.0, float(raw.get("communicationPenalty", cfg.communication_penalty) or cfg.communication_penalty))
    cfg.weather_penalty = max(0.0, float(raw.get("weatherPenalty", cfg.weather_penalty) or cfg.weather_penalty))
    cfg.decoy_penalty = max(0.0, float(raw.get("decoyPenalty", cfg.decoy_penalty) or cfg.decoy_penalty))
    cfg.decoy_saturation_effect = _clamp(float(raw.get("decoySaturationEffect", cfg.decoy_saturation_effect) or cfg.decoy_saturation_effect), 0.0, 1.0)
    return cfg


def config_to_dict(cfg: SwarmConfig) -> dict:
    return asdict(cfg)
