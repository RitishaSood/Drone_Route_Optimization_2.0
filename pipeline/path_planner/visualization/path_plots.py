from __future__ import annotations

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np
from pathlib import Path


def save_path_plot(cost_matrix: np.ndarray, result: dict, output_file: Path) -> None:
    path = result.get("path") or []
    fig, ax = plt.subplots(figsize=(7, 7))
    ax.imshow(cost_matrix, cmap="gray_r", origin="lower")

    if path:
        xs = [p["x"] for p in path]
        ys = [p["y"] for p in path]
        ax.plot(xs, ys, linewidth=2)
        ax.scatter(xs[0], ys[0], c="green", s=35, label="Start")
        ax.scatter(xs[-1], ys[-1], c="red", s=35, label="Goal")
        ax.legend(loc="best")

    ax.set_title(result.get("displayName", result.get("algorithm", "Path")))
    ax.set_xlabel("X")
    ax.set_ylabel("Y")
    fig.tight_layout()
    output_file.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output_file, dpi=150)
    plt.close(fig)


def save_comparison_plot(results: list[dict], output_file: Path) -> None:
    metrics = [r for r in results if r.get("success")]
    if not metrics:
        return

    fig, ax = plt.subplots(figsize=(9, 5))
    labels = [r["displayName"] for r in metrics]
    values = [r.get("totalCost", 0.0) for r in metrics]
    ax.bar(labels, values)
    ax.set_ylabel("Total Cost")
    ax.set_title("Algorithm Comparison")
    fig.tight_layout()
    output_file.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output_file, dpi=150)
    plt.close(fig)
