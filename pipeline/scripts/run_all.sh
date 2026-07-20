#!/bin/sh
set -eu

echo "====================================="
echo " UAV Python + C++ Full Pipeline"
echo "====================================="

ROOT_DIR="/app"
PYTHON_DIR="$ROOT_DIR/pipeline/env_generator"
CPP_EXE="${CPP_EXECUTABLE_NAME:-uav_pipeline}"

export MPLBACKEND=Agg

now_ms() {
    date +%s%3N
}

perf_pipeline_start="$(now_ms)"
perf_python_start=""
perf_cpp_start=""
perf_final_cost_start=""
perf_path_planner_start=""

if [ "${RUN_DIR:-}" ]; then
    case "$RUN_DIR" in
        /*) ACTIVE_RUN_DIR="$RUN_DIR" ;;
        *) ACTIVE_RUN_DIR="$ROOT_DIR/$RUN_DIR" ;;
    esac

    DATA_ROOT_DIR="$ACTIVE_RUN_DIR/data"
    LOGS_DIR="$ACTIVE_RUN_DIR/logs"
    CONFIG_DIR="$ACTIVE_RUN_DIR/config"
else
    DATA_ROOT_DIR="$ROOT_DIR/data"
    LOGS_DIR=""
    CONFIG_DIR=""
fi

CSV_DIR="$DATA_ROOT_DIR/csv"
PLOTS_DIR="$DATA_ROOT_DIR/plots"
OUTPUTS_DIR="$DATA_ROOT_DIR/outputs"
perf_summary_file="$OUTPUTS_DIR/performance_summary.json"

echo ""
echo "[INFO] Root directory: $ROOT_DIR"
if [ "${RUN_DIR:-}" ]; then
    echo "[INFO] Run directory: $ACTIVE_RUN_DIR"
fi

echo ""
echo "[1] Cleaning old generated files"

mkdir -p "$DATA_ROOT_DIR" "$CSV_DIR" "$PLOTS_DIR" "$OUTPUTS_DIR"
if [ "$LOGS_DIR" ]; then
    mkdir -p "$LOGS_DIR" "$CONFIG_DIR"
fi

if [ "${RUN_DIR:-}" ]; then
    ln -sfn "$DATA_ROOT_DIR/outputs" "$ACTIVE_RUN_DIR/outputs"
    ln -sfn "$DATA_ROOT_DIR/plots" "$ACTIVE_RUN_DIR/plots"
fi

find "$CSV_DIR" -mindepth 1 ! -name ".gitkeep" -exec rm -rf {} +
find "$PLOTS_DIR" -mindepth 1 ! -name ".gitkeep" -exec rm -rf {} +
find "$OUTPUTS_DIR" -mindepth 1 ! -name ".gitkeep" -exec rm -rf {} +
if [ "$LOGS_DIR" ]; then
    find "$LOGS_DIR" -mindepth 1 \
        ! -name ".gitkeep" \
        ! -name "pipeline.log" \
        -exec rm -rf {} +
fi

touch "$DATA_ROOT_DIR/.gitkeep"
touch "$CSV_DIR/.gitkeep"
touch "$PLOTS_DIR/.gitkeep"
touch "$OUTPUTS_DIR/.gitkeep"
if [ "$LOGS_DIR" ]; then
    touch "$LOGS_DIR/.gitkeep"
fi

echo "[OK] Cleaned active data, plots, outputs, and logs folders while keeping .gitkeep"

echo ""
echo "[2] Running Python generator"

perf_python_start="$(now_ms)"
cd "$ROOT_DIR"
python pipeline/env_generator/main.py

echo "[OK] Python generator completed"

echo ""
echo "[3] Validating generated CSV files"

cd "$ROOT_DIR"

for file in \
    "$CSV_DIR/terrain_height.csv" \
    "$CSV_DIR/terrain_type.csv" \
    "$CSV_DIR/sensor.csv" \
    "$CSV_DIR/nfz.csv" \
    "$CSV_DIR/env.csv"
do
    if [ ! -f "$file" ]; then
        echo "[ERROR] Missing required file: $file"
        exit 1
    else
        echo "[OK] Found $file"
    fi
done

echo ""
echo "[4] Checking C++ executable"

if ! command -v "$CPP_EXE" >/dev/null 2>&1; then
    echo "[ERROR] C++ executable not found in PATH:"
    echo "$CPP_EXE"
    exit 1
fi

echo "[OK] Found C++ executable: $CPP_EXE"

echo ""
echo "[5] Running C++ engine"

perf_cpp_start="$(now_ms)"
cd "$ROOT_DIR"
"$CPP_EXE"

echo "[OK] C++ pipeline completed"

echo ""
echo "[6] Validating C++ output files"

if [ -f "$OUTPUTS_DIR/final_cost.csv" ]; then
    FINAL_COST_FILE="$OUTPUTS_DIR/final_cost.csv"
elif [ -f "$OUTPUTS_DIR/finalcost.csv" ]; then
    FINAL_COST_FILE="$OUTPUTS_DIR/finalcost.csv"
else
    echo "[ERROR] Missing output file. Checked:"
    echo "$OUTPUTS_DIR/final_cost.csv"
    echo "$OUTPUTS_DIR/finalcost.csv"
    exit 1
fi

echo "[OK] Found final cost file:"
echo "$FINAL_COST_FILE"

echo ""
echo "[7] Checking final cost plot script"

FINAL_COST_PLOT_SCRIPT="$PYTHON_DIR/visualization/finalcsv.py"

if [ -f "$FINAL_COST_PLOT_SCRIPT" ]; then
    echo "[INFO] Generating final cost plots..."
    perf_final_cost_start="$(now_ms)"
    python pipeline/env_generator/visualization/finalcsv.py
    echo "[OK] Final cost plots generated"
else
    echo "[WARN] pipeline/env_generator/visualization/finalcsv.py not found. Skipping final cost plots."
fi

echo ""
echo "[8] Checking path planner"
PATH_PLANNER_MAIN="$ROOT_DIR/pipeline/path_planner/main.py"

if [ ! -f "$PATH_PLANNER_MAIN" ]; then
    echo "[WARN] pipeline/path_planner/main.py not found. Skipping path planner."
else
    if [ ! -f "$OUTPUTS_DIR/final_cost.csv" ] && [ ! -f "$OUTPUTS_DIR/finalcost.csv" ]; then
        echo "[ERROR] final_cost.csv is required before running the path planner"
        exit 1
    fi

    echo "[INFO] Running path planner..."
    perf_path_planner_start="$(now_ms)"
    python pipeline/path_planner/main.py
    echo "[OK] Path planner completed"
fi

perf_end="$(now_ms)"

python - <<'PY' "$perf_summary_file" "$perf_pipeline_start" "$perf_python_start" "$perf_cpp_start" "$perf_final_cost_start" "$perf_path_planner_start" "$perf_end"
import json
import sys
from pathlib import Path

path = Path(sys.argv[1])
start = int(sys.argv[2])
python_start = int(sys.argv[3]) if sys.argv[3] else None
cpp_start = int(sys.argv[4]) if sys.argv[4] else None
final_cost_start = int(sys.argv[5]) if sys.argv[5] else None
path_planner_start = int(sys.argv[6]) if sys.argv[6] else None
end = int(sys.argv[7])

summary = {
    "terrain_generation_ms": None,
    "sensor_generation_ms": None,
    "cpp_field_generation_ms": None,
    "final_cost_generation_ms": None,
    "path_planning_ms": None,
    "lazy_3d_astar_ms": None,
    "monte_carlo_ms": None,
    "plot_generation_ms": None,
    "artifact_discovery_ms": None,
    "total_pipeline_ms": end - start,
}

if python_start:
    summary["terrain_generation_ms"] = python_start - start
    summary["sensor_generation_ms"] = python_start - start
if cpp_start:
    summary["cpp_field_generation_ms"] = cpp_start - python_start if python_start else None
if final_cost_start:
    summary["final_cost_generation_ms"] = final_cost_start - cpp_start if cpp_start else None
if path_planner_start:
    summary["path_planning_ms"] = end - path_planner_start
    summary["plot_generation_ms"] = end - path_planner_start

path.parent.mkdir(parents=True, exist_ok=True)
path.write_text(json.dumps(summary, indent=2), encoding="utf-8")
PY

echo "[OK] Wrote performance summary: $perf_summary_file"

echo ""
echo "====================================="
echo " FULL PIPELINE COMPLETED SUCCESSFULLY"
echo "====================================="

echo ""
echo "CSV input files:"
echo "$CSV_DIR"

echo ""
echo "Plot files:"
echo "$PLOTS_DIR"

echo ""
echo "C++ output files:"
echo "$OUTPUTS_DIR"
