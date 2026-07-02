from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import Any

import numpy as np

if __package__ in {None, ""}:
    sys.path.append(str(Path(__file__).resolve().parents[2]))

from pipeline.path_planner.algorithms import (  # noqa: E402
    run_ant_colony,
    run_astar,
    run_dijkstra,
    run_dstar_lite,
    run_theta_star,
)
from pipeline.path_planner.drone_profiles import get_drone_fuel_profile  # noqa: E402
from pipeline.path_planner.export.planner_exporter import (  # noqa: E402
    export_algorithm_metrics_csv,
    export_algorithm_metrics_json,
    export_path_csv,
)
from pipeline.path_planner.io.cost_loader import load_cost_matrix  # noqa: E402
from pipeline.path_planner.metrics.metrics import enrich_algorithm_result  # noqa: E402


def get_run_root() -> Path:
    run_dir = os.environ.get("RUN_DIR")
    if run_dir:
        root = Path(run_dir)
        if not root.is_absolute():
            root = Path.cwd() / root
        return root.resolve()
    return Path.cwd()


def get_data_root(run_root: Path) -> Path:
    if os.environ.get("RUN_DIR"):
        return run_root / "data"
    return run_root / "data"


def get_outputs_dir(run_root: Path) -> Path:
    if os.environ.get("RUN_DIR"):
        return run_root / "outputs"
    return run_root / "data" / "outputs"


def get_plots_dir(run_root: Path) -> Path:
    if os.environ.get("RUN_DIR"):
        return run_root / "plots"
    return run_root / "data" / "plots"


def read_env_file(env_path: Path) -> dict[str, str]:
    values: dict[str, str] = {}
    if not env_path.exists():
        return values

    for line in env_path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        values[key.strip()] = value.strip()
    return values


def parse_int(values: dict[str, str], key: str, default: int) -> int:
    try:
        return int(values.get(key, default))
    except (TypeError, ValueError):
        return default


def parse_float(values: dict[str, str], key: str, default: float) -> float:
    try:
        return float(values.get(key, default))
    except (TypeError, ValueError):
        return default


def parse_list(values: dict[str, str], key: str, default: list[str]) -> list[str]:
    raw = values.get(key)
    if not raw:
        return default
    return [part.strip() for part in raw.split(",") if part.strip()]


def load_context() -> dict[str, Any]:
    run_root = get_run_root()
    env_path = run_root / "config" / "scenario.env" if os.environ.get("RUN_DIR") else Path("config") / "scenario.env"
    values = read_env_file(env_path)

    flight_z = parse_int(values, "FLIGHT_Z", 50)
    start_x = parse_int(values, "START_X", 0)
    start_y = parse_int(values, "START_Y", 0)
    end_x = parse_int(values, "END_X", 99)
    end_y = parse_int(values, "END_Y", 99)
    start_z = parse_int(values, "START_Z", flight_z)
    end_z = parse_int(values, "END_Z", flight_z)

    if start_x == end_x and start_y == end_y:
        raise ValueError("Start and end cannot be identical")

    if not all(0 <= v <= 99 for v in (start_x, start_y, end_x, end_y)):
        raise ValueError("Route coordinates must be 0..99")

    if not 0 <= flight_z <= 100:
        raise ValueError("FLIGHT_Z must be 0..100")

    algorithms = parse_list(
        values,
        "ALGORITHMS",
        ["dijkstra", "astar", "theta-star", "dstar-lite", "ant-colony"],
    )

    return {
        "run_root": run_root,
        "env_path": env_path,
        "values": values,
        "final_cost_file": get_outputs_dir(run_root) / "final_cost.csv",
        "outputs_dir": get_outputs_dir(run_root),
        "plots_dir": get_plots_dir(run_root),
        "start_xy": (start_x, start_y),
        "goal_xy": (end_x, end_y),
        "start_z": start_z,
        "end_z": end_z,
        "flight_z": flight_z,
        "drone_name": values.get("DRONE_NAME", "IAI Heron"),
        "cell_scale_m": parse_float(values, "CELL_SCALE_M", 1000.0),
        "algorithms": algorithms,
        "threat_threshold": parse_float(values, "THREAT_THRESHOLD", 999999.0),
    }


def run_algorithms(cost_matrix: np.ndarray, context: dict[str, Any]) -> list[dict]:
    run_id = os.environ.get("RUN_ID", "")
    profile = get_drone_fuel_profile(context["drone_name"])
    results: list[dict] = []

    runners = {
        "dijkstra": run_dijkstra,
        "astar": run_astar,
        "theta-star": run_theta_star,
        "dstar-lite": run_dstar_lite,
        "ant-colony": run_ant_colony,
    }

    for name in context["algorithms"]:
        runner = runners.get(name)
        if runner is None:
            continue

        try:
            raw = runner(
                cost_matrix=cost_matrix,
                start_xy=context["start_xy"],
                goal_xy=context["goal_xy"],
                flight_z=context["flight_z"],
                threat_threshold=context["threat_threshold"],
            )
        except Exception as exc:
            raw = {
                "algorithm": name,
                "displayName": name,
                "status": "failed",
                "success": False,
                "runtimeMs": 0.0,
                "totalCost": 0.0,
                "nodesTraversed": 0,
                "nodesVisited": 0,
                "pathNodeCount": 0,
                "path": [],
                "failureReason": str(exc),
                "pathCsv": f"{name.replace('-', '_')}_path.csv",
                "pathPlot": f"{name.replace('-', '_')}_path.png",
            }

        enriched = enrich_algorithm_result(
            raw,
            cost_matrix=cost_matrix,
            drone_profile=profile,
            cell_scale_km=context["cell_scale_m"] / 1000.0,
        )

        if not enriched.get("pathCsv"):
            enriched["pathCsv"] = f"{name.replace('-', '_')}_path.csv"
        if not enriched.get("pathPlot"):
            enriched["pathPlot"] = f"{name.replace('-', '_')}_path.png"

        results.append(enriched)

    return results


def export_paths_and_plots(cost_matrix: np.ndarray, results: list[dict], context: dict[str, Any]) -> None:
    outputs_dir: Path = context["outputs_dir"]
    plots_dir: Path = context["plots_dir"]

    outputs_dir.mkdir(parents=True, exist_ok=True)
    plots_dir.mkdir(parents=True, exist_ok=True)

    for result in results:
        path = result.get("path", [])
        path_rows = []
        cumulative_cost = 0.0
        cumulative_distance = 0.0
        prev_point: dict[str, Any] | None = None

        for point in path:
            x = int(point["x"])
            y = int(point["y"])
            cost = float(cost_matrix[y, x])
            if prev_point is not None:
                dx = x - int(prev_point["x"])
                dy = y - int(prev_point["y"])
                cumulative_distance += (dx * dx + dy * dy) ** 0.5
                cumulative_cost += cost
            else:
                cumulative_cost = cost
            path_rows.append(
                {
                    "x": x,
                    "y": y,
                    "z": int(point["z"]),
                    "cost": cost,
                    "cumulative_cost": cumulative_cost,
                    "distance_km": cumulative_distance * (context["cell_scale_m"] / 1000.0),
                }
            )
            prev_point = point

        export_path_csv(outputs_dir / str(result["pathCsv"]), path_rows)
        # Algorithm visualization is intentionally omitted for now.

    export_algorithm_metrics_json(outputs_dir / "algorithm_metrics.json", results)
    export_algorithm_metrics_csv(outputs_dir / "algorithm_metrics.csv", results)


def main() -> int:
    context = load_context()
    final_cost_file = context["final_cost_file"]
    if not final_cost_file.exists():
        raise FileNotFoundError(f"Missing final_cost.csv at {final_cost_file}")

    cost_matrix = load_cost_matrix(final_cost_file)
    results = run_algorithms(cost_matrix, context)
    export_paths_and_plots(cost_matrix, results, context)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
