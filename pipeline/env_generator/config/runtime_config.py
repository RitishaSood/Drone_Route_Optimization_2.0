from __future__ import annotations

import os
from pathlib import Path


PYTHON_DIR = Path(__file__).resolve().parents[1]
REPO_ROOT = Path(__file__).resolve().parents[3]

_run_dir_value = os.environ.get("RUN_DIR", "").strip()
if _run_dir_value:
    _run_dir_path = Path(_run_dir_value)
    RUN_DIR = _run_dir_path if _run_dir_path.is_absolute() else REPO_ROOT / _run_dir_path
else:
    RUN_DIR = None

if RUN_DIR is not None:
    DATA_ROOT_DIR = RUN_DIR / "data"
    CSV_DIR = DATA_ROOT_DIR / "csv"
    OUTPUTS_DIR = DATA_ROOT_DIR / "outputs"
    PLOTS_DIR = DATA_ROOT_DIR / "plots"
    CONFIG_DIR = RUN_DIR / "config"
    LOGS_DIR = RUN_DIR / "logs"
    SCENARIO_CONFIG_FILE = CONFIG_DIR / "scenario.env"
else:
    DATA_ROOT_DIR = REPO_ROOT / "data"
    CSV_DIR = DATA_ROOT_DIR / "csv"
    OUTPUTS_DIR = DATA_ROOT_DIR / "outputs"
    PLOTS_DIR = DATA_ROOT_DIR / "plots"
    CONFIG_DIR = None
    LOGS_DIR = None
    SCENARIO_CONFIG_FILE = None


def _ensure_directories() -> None:
    for directory in (DATA_ROOT_DIR, CSV_DIR, OUTPUTS_DIR, PLOTS_DIR, CONFIG_DIR, LOGS_DIR):
        if directory is not None:
            directory.mkdir(parents=True, exist_ok=True)


def _parse_scenario_file() -> dict[str, str]:
    values: dict[str, str] = {}

    if SCENARIO_CONFIG_FILE is None or not SCENARIO_CONFIG_FILE.exists():
        return values

    with SCENARIO_CONFIG_FILE.open("r", encoding="utf-8") as file:
        for raw_line in file:
            line = raw_line.strip()

            if not line or line.startswith("#") or "=" not in line:
                continue

            key, value = line.split("=", 1)
            key = key.strip()

            if key:
                values[key] = value.strip()

    return values


_ensure_directories()
SCENARIO = _parse_scenario_file()


def get_int(key: str, default: int) -> int:
    value = SCENARIO.get(key)

    if value is None or value == "":
        return default

    try:
        return int(value)
    except ValueError:
        return default


def get_float(key: str, default: float) -> float:
    value = SCENARIO.get(key)

    if value is None or value == "":
        return default

    try:
        return float(value)
    except ValueError:
        return default


def get_str(key: str, default: str) -> str:
    value = SCENARIO.get(key)

    if value is None or value == "":
        return default

    return value


def get_list(key: str, default: list[str], sep: str = ",") -> list[str]:
    value = SCENARIO.get(key)

    if value is None or value == "":
        return list(default)

    return [
        item.strip()
        for item in value.split(sep)
        if item.strip()
    ]


def get_bool(key: str, default: bool) -> bool:
    value = SCENARIO.get(key)

    if value is None or value == "":
        return default

    return value.lower() in {"1", "true", "yes", "y", "on"}
