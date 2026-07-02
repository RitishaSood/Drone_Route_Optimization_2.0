import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt


class LayerPlot:

    @staticmethod
    def create(
        elevation_layer,
        visibility_layer,
        strategic_layer,
        nfz_mask
    ):

        fig, axes = plt.subplots(
            2,
            2,
            figsize=(12, 10)
        )

        layers = [
            (
                elevation_layer,
                "Elevation Layer",
                "viridis",
                "Normalized Elevation"
            ),
            (
                visibility_layer,
                "Visibility Layer",
                "RdYlGn",
                "Visibility Score"
            ),
            (
                strategic_layer,
                "Strategic Layer",
                "YlOrRd",
                "Strategic Score"
            ),
            (
                nfz_mask,
                "NFZ Mask",
                "Reds",
                "NFZ"
            )
        ]

        for ax, layer in zip(
            axes.flatten(),
            layers
        ):

            data, title, cmap, label = layer

            image = ax.imshow(
                data.T,
                cmap=cmap,
                origin="lower",
                extent=[0, data.shape[0], 0, data.shape[1]]
            )

            ax.set_title(
                title
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
                label
            )

        fig.tight_layout()

        return fig
