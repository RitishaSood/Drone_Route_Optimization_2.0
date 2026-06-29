import matplotlib.pyplot as plt
import numpy as np


class Terrain3DPlot:

    @staticmethod
    def create(
        height_map
    ):

        fig = plt.figure(
            figsize=(12,8)
        )

        ax = fig.add_subplot(
            111,
            projection="3d"
        )

        size = height_map.shape[0]

        x = np.arange(size)
        y = np.arange(size)

        xx, yy = np.meshgrid(
            x,
            y
        )

        surface = ax.plot_surface(
            xx,
            yy,
            height_map,
            cmap="terrain",
            edgecolor="none"
        )

        fig.colorbar(
            surface,
            shrink=0.6
        )

        ax.set_title(
            "3D Terrain Surface"
        )

        ax.set_xlabel("X (km)")
        ax.set_ylabel("Y (km)")
        ax.set_zlabel("Z")

        return fig