import os
import matplotlib.pyplot as plt


class SaveUtils:

    @staticmethod
    def save_figure(
        fig,
        output_dir,
        filename,
        dpi=150
    ):

        os.makedirs(
            output_dir,
            exist_ok=True
        )

        path = os.path.join(
            output_dir,
            filename
        )

        fig.savefig(
            path,
            dpi=dpi,
            bbox_inches="tight"
        )

        plt.close(fig)

        print(
            f"[PLOT] {path}"
        )

        return path