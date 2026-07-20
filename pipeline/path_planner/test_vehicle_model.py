from __future__ import annotations

import json

import numpy as np

from pipeline.path_planner.vehicle_model import summarize_path_performance, summary_to_dict


def main() -> int:
    path_2d = [(0, 0), (1, 0), (2, 1), (3, 1)]
    path_3d = [(0, 0, 50), (1, 0, 50), (2, 1, 55), (3, 1, 55)]
    risk_grid = np.array([[1.0, 2.0, 3.0, 4.0], [1.5, 2.5, 3.5, 4.5]], dtype=float)

    summary_2d = summarize_path_performance(path_2d, risk_lookup=risk_grid, drone_name="IAI Heron")
    summary_3d = summarize_path_performance(path_3d, risk_lookup=risk_grid, drone_name="IAI Heron")

    print(json.dumps(summary_to_dict(summary_2d), indent=2))
    print(json.dumps(summary_to_dict(summary_3d), indent=2))

    for summary in (summary_2d, summary_3d):
        assert summary.total_distance_km > 0
        assert summary.total_time_seconds > 0
        assert summary.total_fuel_used > 0
        assert summary.health_remaining <= summary.health_capacity
        assert summary.transition_count > 0

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
