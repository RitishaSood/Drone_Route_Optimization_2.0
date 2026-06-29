import matplotlib.pyplot as plt
from matplotlib.colors import ListedColormap

from terrain.terrain_constants import (
    WATER,
    PLAIN,
    FOREST,
    HILL,
    VALLEY,
    MOUNTAIN
)


class TerrainPlot:

    @staticmethod
    def create(
        terrain_map
    ):

        colors = [
            "#2B6CB0",  # Water
            "#D9C27C",  # Plain
            "#2F855A",  # Forest
            "#B7791F",  # Hill
            "#718096",  # Valley
            "#4A5568",  # Mountain
        ]

        labels = [
            "Water",
            "Plain",
            "Forest",
            "Hill",
            "Valley",
            "Mountain"
        ]

        cmap = ListedColormap(
            colors
        )

        fig, ax = plt.subplots(
            figsize=(9, 8)
        )

        image = ax.imshow(
            terrain_map,
            cmap=cmap,
            origin="lower",
            vmin=0,
            vmax=5
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
            ticks=[
                WATER,
                PLAIN,
                FOREST,
                HILL,
                VALLEY,
                MOUNTAIN
            ]
        )

        cbar.ax.set_yticklabels(
            labels
        )

        return fig