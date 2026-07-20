from __future__ import annotations

from pathlib import Path

import numpy as np


def load_cost_matrix(final_cost_file: Path) -> np.ndarray:
    if not final_cost_file.exists():
        raise FileNotFoundError(f"Missing final cost file: {final_cost_file}")

    data = np.genfromtxt(final_cost_file, delimiter=",", dtype=float)
    if data.ndim != 2:
        raise ValueError("final_cost.csv must be a 2D CSV grid")
    # The repository treats (0, 0) as the bottom-left grid origin.
    # CSV rows are stored top-to-bottom, so flip vertically when loading.
    return np.flipud(data)
