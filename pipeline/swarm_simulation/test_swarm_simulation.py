from __future__ import annotations

import csv
import json
from pathlib import Path
from tempfile import TemporaryDirectory

from .monte_carlo_engine import run_swarm_study


def _write_route_csv(path: Path, rows: list[dict]) -> None:
    with path.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=["x", "y", "z", "cost", "cumulative_cost", "distance_km"])
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    with TemporaryDirectory() as tmp:
        run_dir = Path(tmp)
        outputs = run_dir / "outputs"
        outputs.mkdir(parents=True, exist_ok=True)
        _write_route_csv(outputs / "astar_path.csv", [
            {"x": 0, "y": 0, "z": 50, "cost": 0.2, "cumulative_cost": 0.2, "distance_km": 0.0},
            {"x": 1, "y": 1, "z": 50, "cost": 0.4, "cumulative_cost": 0.6, "distance_km": 1.0},
            {"x": 2, "y": 2, "z": 50, "cost": 0.3, "cumulative_cost": 0.9, "distance_km": 1.0},
        ])
        _write_route_csv(outputs / "dijkstra_path.csv", [
            {"x": 0, "y": 0, "z": 50, "cost": 0.3, "cumulative_cost": 0.3, "distance_km": 0.0},
            {"x": 0, "y": 1, "z": 50, "cost": 0.2, "cumulative_cost": 0.5, "distance_km": 1.0},
            {"x": 1, "y": 2, "z": 50, "cost": 0.5, "cumulative_cost": 1.0, "distance_km": 1.0},
        ])

        result = run_swarm_study(run_dir, {
            "swarmEnabled": True,
            "swarmSizes": [2, 4],
            "numMonteCarloTrials": 20,
            "strategies": ["single_route", "split_routes", "decoy_lead", "distributed_routing"],
        })

        summary_path = outputs / "swarm_monte_carlo_summary.json"
        trials_path = outputs / "swarm_monte_carlo_trials.csv"
        plots_dir = run_dir / "plots"
        assert summary_path.exists()
        assert trials_path.exists()
        assert result["summary"]
        assert result["trials"]
        assert (plots_dir / "swarm_success_probability.png").exists()
        assert (plots_dir / "swarm_survivors_by_strategy.png").exists()
        assert (plots_dir / "swarm_coverage_by_strategy.png").exists()
        assert (plots_dir / "swarm_cost_by_strategy.png").exists()
        assert (plots_dir / "swarm_success_vs_swarm_size.png").exists()
        assert (plots_dir / "swarm_loss_breakdown.png").exists()
        payload = json.loads(summary_path.read_text(encoding="utf-8"))
        assert payload["summary"]
        assert all("missionSuccessProbability" in row for row in payload["summary"])


if __name__ == "__main__":
    main()
