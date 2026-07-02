import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.colors import ListedColormap

from terrain.terrain_constants import (
    FOREST,
    HILL,
    MOUNTAIN,
    PLAIN,
    VALLEY,
    WATER,
)
from visualization.styles import TERRAIN_COLORS


class TerrainPlot:

    @staticmethod
    def create(
        terrain_map
    ):

        terrain_ids = [
            WATER,
            PLAIN,
            FOREST,
            HILL,
            VALLEY,
            MOUNTAIN
        ]
        labels = [
            "Water",
            "Plain",
            "Forest",
            "Hill",
            "Valley",
            "Mountain"
        ]
        colors = [
            TERRAIN_COLORS[terrain_id]
            for terrain_id in terrain_ids
        ]

        cmap = ListedColormap(
            colors
        )

        fig, ax = plt.subplots(
            figsize=(9, 8)
        )

        image = ax.imshow(
            terrain_map.T,
            cmap=cmap,
            origin="lower",
            vmin=0,
            vmax=5,
            extent=[0, terrain_map.shape[0], 0, terrain_map.shape[1]]
        )

        ax.set_title(
            "Terrain Classification Map"
        )
        ax.set_xlabel(
            "X (km)"
        )
        ax.set_ylabel(
            "Y (km)"
        )

        cbar = fig.colorbar(
            image,
            ax=ax,
            ticks=terrain_ids
        )
        cbar.ax.set_yticklabels(
            labels
        )
        cbar.set_label(
            "Terrain Type"
        )

        fig.tight_layout()

        return fig
