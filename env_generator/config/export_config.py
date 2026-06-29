from dataclasses import dataclass
from pathlib import Path


PYTHON_DIR = Path(__file__).resolve().parents[1]
REPO_ROOT = PYTHON_DIR.parent

DATA_DIR = REPO_ROOT / "data"
PLOTS_DIR = REPO_ROOT / "plots"


@dataclass
class ExportConfig:

    data_dir: str = str(DATA_DIR)
    plots_dir: str = str(PLOTS_DIR)

    terrain_height_csv: str = str(DATA_DIR / "terrain_height.csv")
    terrain_type_csv: str = str(DATA_DIR / "terrain_type.csv")

    sensor_csv: str = str(DATA_DIR / "sensor.csv")
    nfz_csv: str = str(DATA_DIR / "nfz.csv")
    env_csv: str = str(DATA_DIR / "env.csv")