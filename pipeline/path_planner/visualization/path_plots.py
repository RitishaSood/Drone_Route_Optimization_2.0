from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np
from mpl_toolkits.mplot3d import Axes3D  # noqa: F401


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


def save_lazy_3d_route_plot(path: list[dict], output_file: Path) -> None:
    if not path:
        return

    fig = plt.figure(figsize=(8, 6))
    ax = fig.add_subplot(111, projection="3d")
    xs = [p["x"] for p in path]
    ys = [p["y"] for p in path]
    zs = [p["z"] for p in path]

    ax.plot(xs, ys, zs, linewidth=2.5, color="#1f77b4")
    ax.scatter(xs, ys, zs, c=np.linspace(0, 1, len(path)), cmap="viridis", s=18, alpha=0.9)
    ax.scatter(xs[0], ys[0], zs[0], c="green", s=40, label="Start")
    ax.scatter(xs[-1], ys[-1], zs[-1], c="red", s=40, label="Goal")
    ax.set_title("Lazy 3D A* Route")
    ax.set_xlabel("X")
    ax.set_ylabel("Y")
    ax.set_zlabel("Z")
    ax.legend(loc="best")
    ax.view_init(elev=28, azim=-55)
    fig.tight_layout()
    output_file.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output_file, dpi=150)
    plt.close(fig)


def save_lazy_3d_route_over_terrain(path: list[dict], terrain_height: np.ndarray, output_file: Path) -> None:
    if not path:
        return

    fig = plt.figure(figsize=(8, 6))
    ax = fig.add_subplot(111, projection="3d")
    terrain_x = np.arange(terrain_height.shape[1])
    terrain_y = np.arange(terrain_height.shape[0])
    terrain_x, terrain_y = np.meshgrid(terrain_x, terrain_y)
    ax.plot_surface(terrain_x, terrain_y, terrain_height, cmap="terrain", linewidth=0, antialiased=True, alpha=0.8)
    xs = [p["x"] for p in path]
    ys = [p["y"] for p in path]
    zs = [p["z"] for p in path]
    ax.plot(xs, ys, zs, linewidth=3, color="#ffffff")
    ax.scatter(xs, ys, zs, c=np.linspace(0, 1, len(path)), cmap="plasma", s=16, alpha=0.95)
    ax.scatter(xs[0], ys[0], zs[0], c="green", s=40, label="Start")
    ax.scatter(xs[-1], ys[-1], zs[-1], c="red", s=40, label="Goal")
    ax.set_title("Lazy 3D Route Over Terrain")
    ax.set_xlabel("X")
    ax.set_ylabel("Y")
    ax.set_zlabel("Z")
    ax.view_init(elev=35, azim=-60)
    ax.legend(loc="best")
    fig.tight_layout()
    output_file.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output_file, dpi=150)
    plt.close(fig)


def save_lazy_3d_profiles(path: list[dict], output_dir: Path, cost_profile: list[float] | None = None) -> None:
    if not path:
        return

    output_dir.mkdir(parents=True, exist_ok=True)
    xs = list(range(len(path)))
    zs = [p["z"] for p in path]

    altitude_fig, altitude_ax = plt.subplots(figsize=(7, 4))
    altitude_ax.plot(xs, zs, linewidth=2.5, marker="o", markersize=3)
    altitude_ax.set_title("Lazy 3D Altitude Profile")
    altitude_ax.set_xlabel("Path Index")
    altitude_ax.set_ylabel("Altitude (Z)")
    altitude_fig.tight_layout()
    altitude_fig.savefig(output_dir / "lazy_3d_altitude_profile.png", dpi=150)
    plt.close(altitude_fig)

    if cost_profile is None:
        cost_profile = [0.0 for _ in path]

    cost_fig, cost_ax = plt.subplots(figsize=(7, 4))
    cost_ax.plot(xs[: len(cost_profile)], cost_profile, linewidth=2.5, color="#d62728", marker="o", markersize=3)
    cost_ax.set_title("Lazy 3D Cumulative Cost Profile")
    cost_ax.set_xlabel("Path Index")
    cost_ax.set_ylabel("Cumulative Cost")
    cost_fig.tight_layout()
    cost_fig.savefig(output_dir / "lazy_3d_cost_profile.png", dpi=150)
    plt.close(cost_fig)

    segment_fig, segment_ax = plt.subplots(figsize=(7, 4))
    segment_lengths = []
    step_costs = []
    for prev, curr in zip(path, path[1:]):
        dx = curr["x"] - prev["x"]
        dy = curr["y"] - prev["y"]
        dz = curr["z"] - prev["z"]
        segment_lengths.append((dx * dx + dy * dy + dz * dz) ** 0.5)
    step_costs = [curr - prev for prev, curr in zip([0.0] + cost_profile[:-1], cost_profile)]
    segment_ax.plot(xs[1:], segment_lengths, linewidth=2.0, marker="o", label="3D Segment Length")
    segment_ax.plot(xs[: len(step_costs)], step_costs, linewidth=2.0, marker="s", label="Step Cost")
    segment_ax.set_title("Lazy 3D Segment Breakdown")
    segment_ax.set_xlabel("Path Index")
    segment_ax.set_ylabel("Value")
    segment_ax.legend(loc="best")
    segment_fig.tight_layout()
    segment_fig.savefig(output_dir / "lazy_3d_segment_breakdown.png", dpi=150)
    plt.close(segment_fig)


def save_lazy_3d_stats_summary(enriched: dict, output_file: Path) -> None:
    fig, ax = plt.subplots(figsize=(7, 4))
    ax.axis("off")
    lines = [
        f"Success: {enriched.get('success', False)}",
        f"Runtime ms: {enriched.get('runtimeMs', 0.0):.2f}",
        f"Nodes visited: {enriched.get('nodesVisited', 0)}",
        f"Path nodes: {enriched.get('pathNodeCount', 0)}",
        f"Path steps: {enriched.get('pathStepCount', 0)}",
        f"Total distance km: {enriched.get('totalDistanceKm', 0.0):.3f}",
        f"Total cost: {enriched.get('totalCost', 0.0):.6f}",
    ]
    ax.text(0.01, 0.99, "\n".join(lines), va="top", ha="left", family="monospace")
    fig.tight_layout()
    output_file.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output_file, dpi=150)
    plt.close(fig)
