from __future__ import annotations

import json
import tempfile
from pathlib import Path

import numpy as np

from pipeline.path_planner.algorithms.lazy3dastar import run_lazy_3d_astar
from pipeline.path_planner.metrics.metrics import enrich_algorithm_result
from pipeline.path_planner.vehicle_model import EnvironmentState, TransitionWeights, get_drone_profile
from pipeline.path_planner.visualization.path_plots import (
    save_lazy_3d_profiles,
    save_lazy_3d_route_over_terrain,
    save_lazy_3d_route_plot,
    save_lazy_3d_stats_summary,
)


def main() -> int:
    cost_matrix = np.full((100, 100), 1.0, dtype=float)
    terrain_height = np.zeros((100, 100), dtype=float)
    terrain_height[50, 50] = 10.0

    result = run_lazy_3d_astar(
        cost_matrix=cost_matrix,
        start_xyz=(0, 0, 50),
        goal_xyz=(99, 99, 50),
        terrain_height=terrain_height,
        z_min=0,
        z_max=99,
        preferred_z=50,
        altitude_penalty_weight=1.0,
    )
    assert result
    if result["success"]:
        assert result["path"]
        assert all("x" in p and "y" in p and "z" in p for p in result["path"])

    profile = get_drone_profile("IAI Heron")
    enriched = enrich_algorithm_result(
        result,
        cost_matrix=cost_matrix,
        drone_profile=profile,
        cell_scale_km=1.0,
        env=EnvironmentState(),
        weights=TransitionWeights(),
    )
    assert "totalDistanceKm" in enriched
    assert "totalClimbKm" in enriched
    assert "totalDescentKm" in enriched

    with tempfile.TemporaryDirectory() as tmp:
        out = Path(tmp)
        save_lazy_3d_route_plot(result["path"], out / "lazy_3d_route.png")
        save_lazy_3d_route_over_terrain(result["path"], terrain_height, out / "lazy_3d_route_over_terrain.png")
        save_lazy_3d_profiles(result["path"], out, [1.0 for _ in result["path"]])
        save_lazy_3d_stats_summary(enriched, out / "lazy_3d_stats_summary.png")
        for name in [
            "lazy_3d_route.png",
            "lazy_3d_route_over_terrain.png",
            "lazy_3d_altitude_profile.png",
            "lazy_3d_cost_profile.png",
            "lazy_3d_stats_summary.png",
        ]:
            assert (out / name).exists()

    print(json.dumps({
        "success": result["success"],
        "runtimeMs": result["runtimeMs"],
        "nodesVisited": result["nodesVisited"],
        "pathNodeCount": result["pathNodeCount"],
        "totalDistanceKm": enriched["totalDistanceKm"],
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
