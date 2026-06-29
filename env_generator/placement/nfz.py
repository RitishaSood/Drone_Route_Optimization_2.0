import csv
import numpy as np

from matplotlib.path import Path


class NFZLoader:

    @staticmethod
    def build_mask(
        csv_file,
        grid_size=100
    ):

        mask = np.zeros(
            (grid_size, grid_size),
            dtype=np.uint8
        )

        with open(csv_file, newline="") as f:

            reader = csv.DictReader(f)

            for row in reader:

                polygon = [

                    (
                        int(row["x1"]),
                        int(row["y1"])
                    ),

                    (
                        int(row["x2"]),
                        int(row["y2"])
                    ),

                    (
                        int(row["x3"]),
                        int(row["y3"])
                    )
                ]

                NFZLoader._fill_polygon(
                    polygon,
                    mask
                )

        return mask

    @staticmethod
    def _fill_polygon(
        polygon,
        mask
    ):

        poly = Path(polygon)

        min_x = max(
            0,
            int(min(p[0] for p in polygon))
        )

        max_x = min(
            mask.shape[0] - 1,
            int(max(p[0] for p in polygon))
        )

        min_y = max(
            0,
            int(min(p[1] for p in polygon))
        )

        max_y = min(
            mask.shape[1] - 1,
            int(max(p[1] for p in polygon))
        )

        for x in range(
            min_x,
            max_x + 1
        ):
            for y in range(
                min_y,
                max_y + 1
            ):

                if poly.contains_point(
                    (x, y)
                ):
                    mask[x, y] = 1

    @staticmethod
    def is_inside_nfz(
        x,
        y,
        mask
    ):

        if (
            x < 0 or
            y < 0 or
            x >= mask.shape[0] or
            y >= mask.shape[1]
        ):
            return True

        return mask[x, y] == 1