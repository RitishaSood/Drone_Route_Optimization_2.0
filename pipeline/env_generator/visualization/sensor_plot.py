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
from visualization.styles import (
    SENSOR_COLORS,
    SENSOR_MARKERS,
    TERRAIN_COLORS,
)


class SensorPlot:

    @staticmethod
    def create(
        terrain_map,
        sensors
    ):

        terrain_ids = [
            WATER,
            PLAIN,
            FOREST,
            HILL,
            VALLEY,
            MOUNTAIN
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

        cbar = fig.colorbar(
            image,
            ax=ax,
            ticks=terrain_ids
        )
        cbar.set_label(
            "Terrain Type"
        )

        used_labels = set()

        for sensor in sensors:
            marker = SENSOR_MARKERS.get(
                sensor.sensor_type,
                "x"
            )
            color = SENSOR_COLORS.get(
                sensor.sensor_type,
                "black"
            )

            label = sensor.sensor_type

            if label in used_labels:
                label = None
            else:
                used_labels.add(
                    sensor.sensor_type
                )

            ax.scatter(
                sensor.x,
                sensor.y,
                marker=marker,
                color=color,
                s=80,
                edgecolors="black",
                linewidths=0.6,
                label=label
            )

        ax.set_title(
            "Sensor Placement Map"
        )
        ax.set_xlabel(
            "X (km)"
        )
        ax.set_ylabel(
            "Y (km)"
        )
        ax.legend(
            loc="upper right"
        )
        fig.tight_layout()

        return fig
