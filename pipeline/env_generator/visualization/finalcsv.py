from pathlib import Path
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

PYTHON_DIR = Path(__file__).resolve().parents[1]

if str(PYTHON_DIR) not in sys.path:
    sys.path.insert(0, str(PYTHON_DIR))

from config import runtime_config


class FinalCostPlotter:
    def __init__(self, csv_path=None, output_dir=None):
        self.csv_path = (
            Path(csv_path)
            if csv_path
            else runtime_config.OUTPUTS_DIR / "final_cost.csv"
        )
        self.output_dir = (
            Path(output_dir)
            if output_dir
            else runtime_config.PLOTS_DIR
        )

        self.output_dir.mkdir(parents=True, exist_ok=True)

    def load_matrix(self):
        if not self.csv_path.exists():
            raise FileNotFoundError(
                f"Could not find final cost csv at: {self.csv_path}"
            )

        matrix = np.loadtxt(self.csv_path, delimiter=",")

        if matrix.shape != (100, 100):
            raise ValueError(
                f"Expected 100x100 grid, but got shape: {matrix.shape}"
            )

        # CSV is written from top-left. Flip vertically so plot coordinates
        # match the bottom-left grid origin.
        return np.flipud(matrix)

    def plot_binary(self, matrix, threshold=0.0):
        binary = (matrix > threshold).astype(int)

        fig, ax = plt.subplots(figsize=(8, 8))
        image = ax.imshow(
            binary,
            cmap="gray_r",
            origin="lower",
            extent=[0, 100, 0, 100],
            vmin=0,
            vmax=1
        )

        ax.set_title("Binary Final Cost Map (0 vs Non-Zero)")
        ax.set_xlabel("X (km)")
        ax.set_ylabel("Y (km)")
        cbar = fig.colorbar(image, ax=ax, ticks=[0, 1])
        cbar.ax.set_yticklabels(["Zero", "Non-zero"])
        cbar.set_label("Cost Category")
        fig.tight_layout()

        output_path = self.output_dir / "final_cost_binary.png"
        fig.savefig(output_path, dpi=200)
        plt.close(fig)

        print(f"[PLOT] Saved binary plot to: {output_path}")

    def plot_heatmap(self, matrix):
        fig, ax = plt.subplots(figsize=(8, 8))
        image = ax.imshow(
            matrix,
            cmap="hot",
            origin="lower",
            vmin=0.0,
            vmax=1.0,
            extent=[0, 100, 0, 100]
        )

        ax.set_title("Final Cost Heatmap")
        ax.set_xlabel("X (km)")
        ax.set_ylabel("Y (km)")
        cbar = fig.colorbar(image, ax=ax)
        cbar.set_label("Cost / Probability")
        fig.tight_layout()

        output_path = self.output_dir / "final_cost_heatmap.png"
        fig.savefig(output_path, dpi=200)
        plt.close(fig)

        print(f"[PLOT] Saved heatmap to: {output_path}")

    def generate_all(self):
        matrix = self.load_matrix()
        self.plot_binary(matrix)
        self.plot_heatmap(matrix)


if __name__ == "__main__":
    plotter = FinalCostPlotter()
    plotter.generate_all()
