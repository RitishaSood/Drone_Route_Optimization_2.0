from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Iterable


def _ensure_parent(file_path: Path) -> None:
    file_path.parent.mkdir(parents=True, exist_ok=True)


def export_algorithm_metrics_json(output_path: Path, results: list[dict]) -> None:
    _ensure_parent(output_path)
    output_path.write_text(json.dumps({"metrics": results}, indent=2), encoding="utf-8")


def export_algorithm_metrics_csv(output_path: Path, results: list[dict]) -> None:
    _ensure_parent(output_path)
    fieldnames = [
        "algorithm",
        "displayName",
        "status",
        "success",
        "runtimeMs",
        "totalCost",
        "nodesTraversed",
        "nodesVisited",
        "pathNodeCount",
        "totalDistanceKm",
        "turnCount",
        "averageCost",
        "maxCellCost",
        "fuelEstimate",
        "fuelCapacity",
        "fuelRemaining",
        "fuelFeasible",
        "fuelUnit",
        "droneName",
        "droneClass",
        "propulsionClass",
        "failureReason",
        "pathCsv",
        "pathPlot",
    ]
    with output_path.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=fieldnames)
        writer.writeheader()
        for result in results:
            writer.writerow({key: result.get(key) for key in fieldnames})


def export_path_csv(output_path: Path, path: Iterable[dict]) -> None:
    _ensure_parent(output_path)
    with output_path.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(
            fh,
            fieldnames=["x", "y", "z", "cost", "cumulative_cost", "distance_km"],
        )
        writer.writeheader()
        for row in path:
            writer.writerow(row)
