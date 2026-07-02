import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt


class SuitabilityPlot:

    @staticmethod
    def create(
        suitability_maps
    ):

        fig, axes = plt.subplots(
            2,
            2,
            figsize=(12, 10)
        )

        sensor_order = [
            "radar",
            "infrared",
            "visual",
            "acoustic"
        ]

        for ax, sensor in zip(
            axes.flatten(),
            sensor_order
        ):

            image = ax.imshow(
                suitability_maps[sensor].T,
                cmap="plasma",
                origin="lower",
                vmin=0,
                vmax=1,
                extent=[
                    0,
                    suitability_maps[sensor].shape[0],
                    0,
                    suitability_maps[sensor].shape[1]
                ]
            )

            ax.set_title(
                f"{sensor.capitalize()} Suitability"
            )
            ax.set_xlabel(
                "X (km)"
            )
            ax.set_ylabel(
                "Y (km)"
            )

            cbar = fig.colorbar(
                image,
                ax=ax
            )
            cbar.set_label(
                "Suitability Score"
            )

        fig.tight_layout()

        return fig
