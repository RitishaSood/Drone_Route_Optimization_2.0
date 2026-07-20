from __future__ import annotations

import csv
import json
from pathlib import Path
from random import Random
from statistics import median

from .swarm_config import SwarmConfig, config_to_dict, normalize_swarm_config
from .swarm_metrics import TrialResult, summarize_trials
from .swarm_plots import save_swarm_plots
from .swarm_strategies import RouteCandidate, choose_routes
from .threat_sampler import sample_trial_parameters


def _clamp(value: float, low: float = 0.0, high: float = 1.0) -> float:
    return max(low, min(high, value))


def _load_route_candidates(run_dir: Path) -> list[RouteCandidate]:
    outputs_dir = run_dir / "outputs"
    candidates: list[RouteCandidate] = []
    for path_csv in sorted(outputs_dir.glob("*_path.csv")):
        points: list[dict] = []
        with path_csv.open("r", encoding="utf-8", newline="") as fh:
            reader = csv.DictReader(fh)
            for row in reader:
                points.append({
                    "x": int(float(row.get("x", 0) or 0)),
                    "y": int(float(row.get("y", 0) or 0)),
                    "z": int(float(row.get("z", 0) or 0)),
                    "cost": float(row.get("cost", 0) or 0.0),
                    "cumulative_cost": float(row.get("cumulative_cost", 0) or 0.0),
                    "distance_km": float(row.get("distance_km", 0) or 0.0),
                })
        if not points:
            continue
        total_cost = float(points[-1].get("cumulative_cost") or sum(p["cost"] for p in points))
        max_cost = max((p["cost"] for p in points), default=1.0) or 1.0
        risk_profile = [_clamp(p["cost"] / max_cost, 0.0, 1.0) for p in points]
        ew_exposure = _clamp(sum(risk_profile) / max(1, len(risk_profile)), 0.0, 1.0)
        candidates.append(RouteCandidate(path_csv.stem, points, total_cost, risk_profile, ew_exposure))

    if candidates:
        return candidates

    fallback = [
        {"x": 0, "y": 0, "z": 50, "cost": 0.2, "cumulative_cost": 0.2, "distance_km": 0.0},
        {"x": 50, "y": 50, "z": 50, "cost": 0.3, "cumulative_cost": 0.5, "distance_km": 1.0},
        {"x": 99, "y": 99, "z": 50, "cost": 0.4, "cumulative_cost": 0.9, "distance_km": 1.0},
    ]
    return [RouteCandidate("fallback_route", fallback, 0.9, [0.2, 0.3, 0.4], 0.3)]


def _simulate_drone(rng: Random, route: RouteCandidate, sampled: dict, config: SwarmConfig, strategy: str, decoy: bool, main_route_bonus: float) -> tuple[bool, dict]:
    detect_route = 0.0
    for step_risk in route.risk_profile:
        detect_step = _clamp(step_risk * sampled["radar_scale"] * (1.0 + 0.5 * sampled["weather_severity"]))
        detect_route = 1.0 - (1.0 - detect_route) * (1.0 - detect_step)
    detected = rng.random() < detect_route
    exposure_modifier = _clamp(route.ew_exposure + route.route_cost / (len(route.points) + 1.0), 0.2, 1.0)
    sam_kill_probability = sampled["sam_kill_probability"] * exposure_modifier
    if strategy == "decoy_lead" and not decoy:
        sam_kill_probability *= (1.0 - config.decoy_saturation_effect)
    sam_kill = detected and (rng.random() < sam_kill_probability)
    comm_loss_risk = _clamp(sampled["communication_loss"] + sampled["ew_effectiveness"] * route.ew_exposure * (0.75 if decoy else 1.0))
    communication_lost = rng.random() < comm_loss_risk
    weather_failure_risk = _clamp(0.02 + 0.1 * sampled["weather_severity"])
    weather_failure = rng.random() < weather_failure_risk
    destroyed = sam_kill
    survived = not destroyed and not weather_failure and not communication_lost
    route_cost = route.route_cost * (0.9 if decoy else 1.0) * main_route_bonus
    mission_cost = route_cost * 5.0
    return survived, {
        "detected": detected,
        "sam_kill": sam_kill,
        "communication_lost": communication_lost,
        "weather_failure": weather_failure,
        "mission_cost": mission_cost,
        "route_cost": route_cost,
        "decoy": decoy,
    }


def run_swarm_study(run_dir: Path, swarm_config: dict | SwarmConfig | None = None) -> dict:
    config = swarm_config if isinstance(swarm_config, SwarmConfig) else normalize_swarm_config(swarm_config)
    route_pool = _load_route_candidates(run_dir)
    if not config.swarm_enabled:
        return {"available": False, "message": "Swarm simulation is disabled.", "summary": [], "trials": []}

    rng = Random(1337)
    all_trials: list[dict] = []
    summary_rows: list[dict] = []

    for strategy in config.strategies:
        for swarm_size in config.swarm_sizes:
            trial_results: list[TrialResult] = []
            for trial_id in range(1, config.num_monte_carlo_trials + 1):
                sampled = sample_trial_parameters(rng, config)
                assignment = choose_routes(strategy, swarm_size, route_pool, config.decoy_fraction)
                assignments = assignment["assignments"]
                surviving = detected = sam_kills = comm_loss = weather_failures = destroyed = 0
                total_cost = 0.0
                for index, route in enumerate(assignments):
                    is_decoy = strategy == "decoy_lead" and index < assignment["decoy_count"]
                    survived, metrics = _simulate_drone(
                        rng,
                        route,
                        sampled,
                        config,
                        strategy,
                        is_decoy,
                        1.0 if strategy != "single_route" else 0.95,
                    )
                    detected += int(metrics["detected"])
                    sam_kills += int(metrics["sam_kill"])
                    comm_loss += int(metrics["communication_lost"])
                    weather_failures += int(metrics["weather_failure"])
                    destroyed += int(metrics["sam_kill"])
                    total_cost += float(metrics["mission_cost"])
                    if survived:
                        surviving += 1
                required_coverage_drones = max(1, int((swarm_size * config.target_coverage_threshold) + 0.999999))
                target_coverage = min(1.0, surviving / required_coverage_drones)
                mission_completed = surviving >= config.required_survivors and target_coverage >= config.target_coverage_threshold
                total_cost += destroyed * config.lost_drone_penalty
                total_cost += comm_loss * config.communication_penalty
                total_cost += weather_failures * config.weather_penalty
                total_cost += assignment["decoy_count"] * config.decoy_penalty
                trial = TrialResult(
                    trial_id=trial_id,
                    strategy=strategy,
                    swarm_size=swarm_size,
                    surviving_drones=surviving,
                    destroyed_drones=destroyed,
                    detected_drones=detected,
                    sam_kills=sam_kills,
                    communication_loss_events=comm_loss,
                    weather_failures=weather_failures,
                    target_coverage=target_coverage,
                    mission_completed=mission_completed,
                    mission_cost=total_cost,
                    route_diversity=assignment["route_diversity"],
                    decoy_count=assignment["decoy_count"],
                )
                trial_results.append(trial)
                all_trials.append({
                    "trialId": trial_id,
                    "strategy": strategy,
                    "swarmSize": swarm_size,
                    "survivingDrones": surviving,
                    "destroyedDrones": destroyed,
                    "detectedDrones": detected,
                    "samKills": sam_kills,
                    "communicationLossEvents": comm_loss,
                    "weatherFailures": weather_failures,
                    "targetCoverage": target_coverage,
                    "missionCompleted": mission_completed,
                    "missionCost": total_cost,
                    "routeDiversity": assignment["route_diversity"],
                    "decoyCount": assignment["decoy_count"],
                })
            summary_rows.append(summarize_trials(strategy, swarm_size, trial_results))

    outputs_dir = run_dir / "outputs"
    plots_dir = run_dir / "plots"
    outputs_dir.mkdir(parents=True, exist_ok=True)
    plots_dir.mkdir(parents=True, exist_ok=True)
    (outputs_dir / "swarm_config_used.json").write_text(json.dumps(config_to_dict(config), indent=2), encoding="utf-8")
    (outputs_dir / "swarm_monte_carlo_summary.json").write_text(json.dumps({"summary": summary_rows}, indent=2), encoding="utf-8")
    with (outputs_dir / "swarm_monte_carlo_summary.csv").open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=list(summary_rows[0].keys()) if summary_rows else [])
        if summary_rows:
            writer.writeheader()
            writer.writerows(summary_rows)
    with (outputs_dir / "swarm_monte_carlo_trials.csv").open("w", newline="", encoding="utf-8") as fh:
        fieldnames = list(all_trials[0].keys()) if all_trials else []
        writer = csv.DictWriter(fh, fieldnames=fieldnames)
        if all_trials:
            writer.writeheader()
            writer.writerows(all_trials)
    (outputs_dir / "swarm_strategy_routes.json").write_text(
        json.dumps({
            "routes": [
                {
                    "routeId": route.route_id,
                    "routeCost": route.route_cost,
                    "points": route.points,
                }
                for route in route_pool
            ]
        }, indent=2),
        encoding="utf-8",
    )
    save_swarm_plots(summary_rows, plots_dir)
    best = min(summary_rows, key=lambda row: (-float(row["missionSuccessProbability"]), float(row["averageMissionCost"]), row["swarmSize"])) if summary_rows else None
    return {
        "available": True,
        "best": best,
        "summary": summary_rows,
        "trials": all_trials,
        "config": config_to_dict(config),
    }

