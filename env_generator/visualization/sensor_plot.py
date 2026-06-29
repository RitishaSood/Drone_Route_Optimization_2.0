import matplotlib.pyplot as plt
from matplotlib.colors import ListedColormap


class SensorPlot:

    @staticmethod
    def create(
        terrain_map,
        sensors
    ):

        colors = [
            "#2B6CB0",  # Water
            "#D9C27C",  # Plain
            "#2F855A",  # Forest
            "#B7791F",  # Hill
            "#718096",  # Valley
            "#4A5568",  # Mountain
        ]

        cmap = ListedColormap(
            colors
        )

        sensor_styles = {
            "radar": ("^", "red"),
            "infrared": ("s", "orange"),
            "visual": ("D", "lime"),
            "acoustic": ("o", "blue"),
        }

        fig, ax = plt.subplots(
            figsize=(9, 8)
        )

        ax.imshow(
            terrain_map,
            cmap=cmap,
            origin="lower",
            vmin=0,
            vmax=5
        )

        used_labels = set()

        for sensor in sensors:

            marker, color = sensor_styles.get(
                sensor.sensor_type,
                ("x", "black")
            )

            label = sensor.sensor_type

            if label in used_labels:
                label = None
            else:
                used_labels.add(
                    sensor.sensor_type
                )

            ax.scatter(
                sensor.y,
                sensor.x,
                marker=marker,
                color=color,
                s=70,
                edgecolors="black",
                linewidths=0.5,
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

        return fig