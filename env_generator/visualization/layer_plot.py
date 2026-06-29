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
            figsize=(12,10)
        )

        layers = [

            (
                elevation_layer,
                "Elevation Layer",
                "viridis"
            ),

            (
                visibility_layer,
                "Visibility Layer",
                "RdYlGn"
            ),

            (
                strategic_layer,
                "Strategic Layer",
                "YlOrRd"
            ),

            (
                nfz_mask,
                "NFZ Mask",
                "Reds"
            )
        ]

        for ax, layer in zip(
            axes.flatten(),
            layers
        ):

            data, title, cmap = layer

            image = ax.imshow(
                data,
                cmap=cmap,
                origin="lower"
            )

            ax.set_title(title)

            plt.colorbar(
                image,
                ax=ax
            )

        fig.tight_layout()

        return fig