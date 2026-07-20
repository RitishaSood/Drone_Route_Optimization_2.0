from __future__ import annotations

import os
import tempfile
from pathlib import Path

import matplotlib

os.environ.setdefault("MPLCONFIGDIR", str(Path(tempfile.gettempdir()) / "matplotlib"))
matplotlib.use("Agg")
import matplotlib.pyplot as plt


def _save_bar(labels: list[str], values: list[float], title: str, ylabel: str, output_file: Path) -> None:
    output_file.parent.mkdir(parents=True, exist_ok=True)
    fig, ax = plt.subplots(figsize=(8, 4.5))
    ax.bar(labels, values, color="#2457a7")
    ax.set_title(title)
    ax.set_ylabel(ylabel)
    ax.set_ylim(bottom=0)
    ax.grid(axis="y", alpha=0.2)
    fig.tight_layout()
    fig.savefig(output_file, dpi=150)
    plt.close(fig)


def save_swarm_plots(summary_rows: list[dict], output_dir: Path) -> None:
    if not summary_rows:
        return
    output_dir.mkdir(parents=True, exist_ok=True)
    labels = [f"{row['strategy']} / {row['swarmSize']}" for row in summary_rows]
    _save_bar(labels, [float(row.get("missionSuccessProbability") or 0.0) for row in summary_rows], "Mission Success Probability", "Probability", output_dir / "swarm_success_probability.png")
    _save_bar(labels, [float(row.get("averageSurvivingDrones") or 0.0) for row in summary_rows], "Average Surviving Drones", "Drones", output_dir / "swarm_survivors_by_strategy.png")
    _save_bar(labels, [float(row.get("averageTargetCoverage") or 0.0) for row in summary_rows], "Average Target Coverage", "Coverage", output_dir / "swarm_coverage_by_strategy.png")
    _save_bar(labels, [float(row.get("averageMissionCost") or 0.0) for row in summary_rows], "Average Mission Cost", "Cost", output_dir / "swarm_cost_by_strategy.png")

    fig, ax = plt.subplots(figsize=(8, 4.5))
    by_strategy = {}
    for row in summary_rows:
        by_strategy.setdefault(row["strategy"], []).append((int(row["swarmSize"]), float(row.get("missionSuccessProbability") or 0.0)))
    for strategy, points in by_strategy.items():
        points = sorted(points)
        ax.plot([p[0] for p in points], [p[1] for p in points], marker="o", label=strategy)
    ax.set_title("Success vs Swarm Size")
    ax.set_xlabel("Swarm Size")
    ax.set_ylabel("Success Probability")
    ax.grid(alpha=0.2)
    ax.legend()
    fig.tight_layout()
    fig.savefig(output_dir / "swarm_success_vs_swarm_size.png", dpi=150)
    plt.close(fig)

    fig, ax = plt.subplots(figsize=(8, 4.5))
    metrics = [
        ("Detection", "averageDetectionEvents"),
        ("SAM Kills", "averageSAMKills"),
        ("Comm Loss", "averageCommunicationLossEvents"),
        ("Weather", "averageWeatherFailures"),
    ]
    x = range(len(summary_rows))
    bottom = [0.0] * len(summary_rows)
    for label, key in metrics:
        vals = [float(row.get(key) or 0.0) for row in summary_rows]
        ax.bar(x, vals, bottom=bottom, label=label)
        bottom = [a + b for a, b in zip(bottom, vals)]
    ax.set_xticks(list(x))
    ax.set_xticklabels(labels, rotation=45, ha="right")
    ax.set_title("Loss Breakdown")
    ax.legend()
    fig.tight_layout()
    fig.savefig(output_dir / "swarm_loss_breakdown.png", dpi=150)
    plt.close(fig)
