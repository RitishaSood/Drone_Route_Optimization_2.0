from dataclasses import dataclass

from config import runtime_config

DATA_ROOT_DIR = runtime_config.DATA_ROOT_DIR
CSV_DIR = runtime_config.CSV_DIR
OUTPUTS_DIR = runtime_config.OUTPUTS_DIR
PLOTS_DIR = runtime_config.PLOTS_DIR


@dataclass
class ExportConfig:

    data_root_dir: str = str(DATA_ROOT_DIR)
    csv_dir: str = str(CSV_DIR)
    outputs_dir: str = str(OUTPUTS_DIR)
    plots_dir: str = str(PLOTS_DIR)

    data_dir: str = str(CSV_DIR)
    terrain_height_csv: str = str(CSV_DIR / "terrain_height.csv")
    terrain_type_csv: str = str(CSV_DIR / "terrain_type.csv")

    sensor_csv: str = str(CSV_DIR / "sensor.csv")
    nfz_csv: str = str(CSV_DIR / "nfz.csv")
    env_csv: str = str(CSV_DIR / "env.csv")
    final_cost_csv: str = str(OUTPUTS_DIR / "final_cost.csv")
