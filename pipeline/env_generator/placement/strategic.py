import numpy as np

class StrategicLayerGenerator:

    @staticmethod
    def build(
        grid_size,
        high_ground_positions,
        sigma=8
    ):

        layer = np.zeros(
            (grid_size, grid_size),
            dtype=np.float32
        )

        xx, yy = np.meshgrid(
            np.arange(grid_size),
            np.arange(grid_size)
        )

        for x, y in high_ground_positions:

            influence = np.exp(
                -(
                    (xx-x)**2 +
                    (yy-y)**2
                )/(2*sigma*sigma)
            )

            layer += influence

        if layer.max() > 0:
            layer /= layer.max()

        return layer