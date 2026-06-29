import matplotlib
matplotlib.use("Agg")

from pathlib import Path
import numpy as np
import matplotlib.pyplot as plt


class FinalCostPlotter:
    def __init__(self, csv_path=None, output_dir=None):
        # File location:
        # Drone/env_generator/visualization/finalcsv.py
        #
        # parents[0] = Drone/env_generator/visualization
        # parents[1] = Drone/env_generator
        # parents[2] = Drone

        self.repo_root = Path(__file__).resolve().parents[2]

        self.csv_path = Path(csv_path) if csv_path else self.repo_root / "outputs" / "final_cost.csv"
        self.output_dir = Path(output_dir) if output_dir else self.repo_root / "plots"

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

        # CSV is written from top-left.
        # Your coordinate origin is bottom-left.
        # Flip vertically so plot coordinates match your grid.
        matrix = np.flipud(matrix)

        return matrix

    def plot_binary(self, matrix, threshold=0.0):
        binary = (matrix > threshold).astype(int)

        plt.figure(figsize=(8, 8))
        plt.imshow(
            binary,
            cmap="gray_r",
            origin="lower",
            extent=[0, 100, 0, 100]
        )

        plt.title("Binary Final Cost Map (0 vs Non-Zero)")
        plt.xlabel("X")
        plt.ylabel("Y")
        plt.colorbar(label="0 = Free, 1 = Non-Zero Cost")
        plt.tight_layout()

        output_path = self.output_dir / "final_cost_binary.png"
        plt.savefig(output_path, dpi=200)
        plt.close()

        print(f"[PLOT] Saved binary plot to: {output_path}")

    def plot_heatmap(self, matrix):
        plt.figure(figsize=(8, 8))
        plt.imshow(
            matrix,
            cmap="hot",
            origin="lower",
            vmin=0.0,
            vmax=1.0,
            extent=[0, 100, 0, 100]
        )

        plt.title("Final Cost Heatmap")
        plt.xlabel("X")
        plt.ylabel("Y")
        plt.colorbar(label="Cost / Probability")
        plt.tight_layout()

        output_path = self.output_dir / "final_cost_heatmap.png"
        plt.savefig(output_path, dpi=200)
        plt.close()

        print(f"[PLOT] Saved heatmap to: {output_path}")

    def generate_all(self):
        matrix = self.load_matrix()
        self.plot_binary(matrix)
        self.plot_heatmap(matrix)


if __name__ == "__main__":
    plotter = FinalCostPlotter()
    plotter.generate_all()