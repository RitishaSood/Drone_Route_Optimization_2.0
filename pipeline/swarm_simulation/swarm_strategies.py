from __future__ import annotations

from dataclasses import dataclass


@dataclass
class RouteCandidate:
    route_id: str
    points: list[dict]
    route_cost: float
    risk_profile: list[float]
    ew_exposure: float


def rank_routes(routes: list[RouteCandidate]) -> list[RouteCandidate]:
    return sorted(routes, key=lambda route: (route.route_cost, len(route.points)))


def choose_routes(strategy: str, swarm_size: int, routes: list[RouteCandidate], decoy_fraction: float) -> dict:
    ordered = rank_routes(routes)
    if not ordered:
        return {"assignments": [], "route_diversity": 0, "decoy_count": 0}

    if strategy == "single_route":
        chosen = ordered[0]
        return {
            "assignments": [chosen for _ in range(swarm_size)],
            "route_diversity": 1,
            "decoy_count": 0,
        }

    if strategy == "split_routes":
        assignments = [ordered[i % len(ordered)] for i in range(swarm_size)]
        return {
            "assignments": assignments,
            "route_diversity": len({route.route_id for route in assignments}),
            "decoy_count": 0,
        }

    if strategy == "decoy_lead":
        decoy_count = max(1, int(round(swarm_size * decoy_fraction))) if swarm_size > 1 else 0
        safe_route = ordered[0]
        lead_route = ordered[-1]
        assignments = []
        for index in range(swarm_size):
            assignments.append(lead_route if index < decoy_count else safe_route)
        return {
            "assignments": assignments,
            "route_diversity": len({route.route_id for route in assignments}),
            "decoy_count": decoy_count,
        }

    assignments = [ordered[i % len(ordered)] for i in range(swarm_size)]
    return {
        "assignments": assignments,
        "route_diversity": len({route.route_id for route in assignments}),
        "decoy_count": 0,
    }

