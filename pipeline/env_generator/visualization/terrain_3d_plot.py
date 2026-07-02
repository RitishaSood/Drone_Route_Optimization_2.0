import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np


class Terrain3DPlot:

    @staticmethod
    def create(
        height_map
    ):

        fig = plt.figure(
            figsize=(12, 8)
        )

        ax = fig.add_subplot(
            111,
            projection="3d"
        )

        size_x, size_y = height_map.shape
        x = np.arange(size_x)
        y = np.arange(size_y)

        xx, yy = np.meshgrid(
            x,
            y,
            indexing="ij"
        )

        surface = ax.plot_surface(
            xx,
            yy,
            height_map,
            cmap="terrain",
            edgecolor="none",
            linewidth=0,
            antialiased=True
        )

        cbar = fig.colorbar(
            surface,
            ax=ax,
            shrink=0.6,
            pad=0.1
        )
        cbar.set_label(
            "Height (z units)"
        )

        ax.set_title(
            "3D Terrain Surface"
        )
        ax.set_xlabel("X (km)")
        ax.set_ylabel("Y (km)")
        ax.set_zlabel("Z")

        fig.tight_layout()

        return fig
