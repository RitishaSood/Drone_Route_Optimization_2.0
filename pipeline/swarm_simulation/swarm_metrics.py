from __future__ import annotations

from dataclasses import dataclass
from statistics import median


@dataclass
class TrialResult:
    trial_id: int
    strategy: str
    swarm_size: int
    surviving_drones: int
    destroyed_drones: int
    detected_drones: int
    sam_kills: int
    communication_loss_events: int
    weather_failures: int
    target_coverage: float
    mission_completed: bool
    mission_cost: float
    route_diversity: int
    decoy_count: int


def _safe_mean(values: list[float]) -> float:
    return sum(values) / len(values) if values else 0.0


def summarize_trials(strategy: str, swarm_size: int, trials: list[TrialResult]) -> dict:
    surviving = [t.surviving_drones for t in trials]
    destroyed = [t.destroyed_drones for t in trials]
    detected = [t.detected_drones for t in trials]
    sam_kills = [t.sam_kills for t in trials]
    comm = [t.communication_loss_events for t in trials]
    weather = [t.weather_failures for t in trials]
    coverage = [t.target_coverage for t in trials]
    costs = [t.mission_cost for t in trials]
    successful = [t for t in trials if t.mission_completed]
    success_probability = len(successful) / len(trials) if trials else 0.0
    return {
        "swarmSize": swarm_size,
        "strategy": strategy,
        "numTrials": len(trials),
        "missionSuccessProbability": success_probability,
        "averageSurvivingDrones": _safe_mean(surviving),
        "medianSurvivingDrones": float(median(surviving)) if surviving else 0.0,
        "averageDestroyedDrones": _safe_mean(destroyed),
        "averageTargetCoverage": _safe_mean(coverage),
        "averageMissionCost": _safe_mean(costs),
        "averageDetectionEvents": _safe_mean(detected),
        "averageSAMKills": _safe_mean(sam_kills),
        "averageCommunicationLossEvents": _safe_mean(comm),
        "averageWeatherFailures": _safe_mean(weather),
        "survivalRate": _safe_mean([1.0 if v > 0 else 0.0 for v in surviving]),
        "costPerSuccessfulMission": _safe_mean([t.mission_cost for t in successful]) if successful else None,
        "bestCaseSurvivors": max(surviving) if surviving else 0,
        "worstCaseSurvivors": min(surviving) if surviving else 0,
    }

