import matplotlib.pyplot as plt


class SuitabilityPlot:

    @staticmethod
    def create(
        suitability_maps
    ):

        fig, axes = plt.subplots(
            2,
            2,
            figsize=(12,10)
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
                suitability_maps[sensor],
                cmap="plasma",
                origin="lower",
                vmin=0,
                vmax=1
            )

            ax.set_title(
                f"{sensor.capitalize()} Suitability"
            )

            plt.colorbar(
                image,
                ax=ax
            )

        fig.tight_layout()

        return fig