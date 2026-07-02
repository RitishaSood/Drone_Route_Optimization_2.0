from terrain.terrain_generator import TerrainGenerator
from terrain.terrain_exporter import TerrainExporter

from placement.layer_builder import LayerBuilder
from placement.placement_engine import PlacementEngine
from placement.nfz_generator import NFZGenerator

from config.terrain_config import TerrainConfig
from config.sensor_config import SensorConfig
from config.placement_config import PlacementConfig
from config.export_config import ExportConfig
from config.env_config import EnvConfig
from config import runtime_config

from export.exporter import Exporter

from visualization.visualization_manager import VisualizationManager

import random


SENSOR_TYPE_ALIASES = {
    "radar": "radar",
    "ir": "infrared",
    "infrared": "infrared",
    "visual": "visual",
    "acoustic": "acoustic",
}


def _configured_sensor_counts(sensor_cfg):
    default_counts = {
        "radar": sensor_cfg.radar_count,
        "infrared": sensor_cfg.infrared_count,
        "visual": sensor_cfg.visual_count,
        "acoustic": sensor_cfg.acoustic_count,
    }

    requested_types = runtime_config.get_list(
        "THREAT_TYPES",
        list(default_counts.keys())
    )

    enabled_types = []

    for sensor_type in requested_types:
        normalized = SENSOR_TYPE_ALIASES.get(sensor_type.strip().lower())

        if normalized and normalized not in enabled_types:
            enabled_types.append(normalized)

    if not enabled_types:
        enabled_types = list(default_counts.keys())

    sensor_total_value = runtime_config.SCENARIO.get("SENSOR_COUNT")

    if sensor_total_value is None:
        return {
            sensor_type: default_counts[sensor_type]
            if sensor_type in enabled_types
            else 0
            for sensor_type in default_counts
        }

    sensor_total = runtime_config.get_int(
        "SENSOR_COUNT",
        sum(default_counts.values())
    )

    if sensor_total <= 0:
        return {
            sensor_type: 0
            for sensor_type in default_counts
        }

    base_count = sensor_total // len(enabled_types)
    remainder = sensor_total % len(enabled_types)

    counts = {
        sensor_type: 0
        for sensor_type in default_counts
    }

    for index, sensor_type in enumerate(enabled_types):
        counts[sensor_type] = base_count + (1 if index < remainder else 0)

    return counts


def main():

    print("\n==============================")
    print(" UAV Sensor Placement System ")
    print("==============================\n")

    # ----------------------------------
    # Configs
    # ----------------------------------

    terrain_cfg = TerrainConfig(
        seed=runtime_config.get_int(
            "TERRAIN_SEED",
            42
        )
    )
    sensor_cfg = SensorConfig()
    placement_cfg = PlacementConfig()
    export_cfg = ExportConfig()
    env_cfg = EnvConfig()
    placement_mode = runtime_config.get_str(
        "PLACEMENT_MODE",
        "greedy"
    ).lower()

    # ----------------------------------
    # Seed
    # ----------------------------------

    seed = terrain_cfg.seed

    if seed is None:
        seed = random.randint(
            0,
            100000
        )

    terrain_cfg.seed = seed

    print(f"[INFO] Seed = {seed}")
    print(f"[INFO] CSV dir = {export_cfg.csv_dir}")
    print(f"[INFO] Plots dir = {export_cfg.plots_dir}")

    if placement_mode != "greedy":
        print(
            f"[WARN] Unsupported PLACEMENT_MODE={placement_mode}; using greedy"
        )

    # ----------------------------------
    # Terrain Generation
        # ----------------------------------
    print("[1] Generating Terrain", flush=True)

    tg = TerrainGenerator(
        terrain_cfg
    )

    print("[DEBUG] TerrainGenerator created", flush=True)

    height_map, terrain_map = tg.generate()

    print("[DEBUG] Terrain generated successfully", flush=True)
    # ----------------------------------
    # Export Terrain
    # ----------------------------------

    print("\n[2] Exporting Terrain CSVs")

    TerrainExporter.export(
        height_map,
        terrain_map,
        output_dir=export_cfg.csv_dir
    )

    # ----------------------------------
    # NFZ Generation + Export
    # ----------------------------------

    print("\n[3a] Generating NFZs")

    nfz_polygons = NFZGenerator.generate(
        seed=seed,
        count=runtime_config.get_int(
            "NFZ_COUNT",
            4
        )
    )

    exporter = Exporter(
        export_cfg
    )

    exporter.export_nfz(
        nfz_polygons
    )
     # ----------------------------------
    # Env.csv builder
    # ----------------------------------

    print("\n[3b] Exporting Environment CSV")

    exporter.export_env(
        env_cfg
    )

    # ----------------------------------
    # Layer Builder
    # ----------------------------------

    print("\n[4] Building Layers")

    lb = LayerBuilder(
        tg,
        nfz_file=export_cfg.nfz_csv
    )

    print("Layers Generated")

    # ----------------------------------
    # Sensor Counts
    # ----------------------------------

    sensor_counts = _configured_sensor_counts(
        sensor_cfg
    )

    print("\nSensor Counts:")

    for key, value in sensor_counts.items():
        print(f"  {key:<10} : {value}")

    # ----------------------------------
    # Placement
    # ----------------------------------

    print("\n[5] Running Placement Engine")

    engine = PlacementEngine(
        tg,
        lb,
        placement_cfg
    )

    placed_sensors = engine.place(
        sensor_counts
    )

    print(f"{len(placed_sensors)} sensors placed")

    # ----------------------------------
    # Export Sensors
    # ----------------------------------

    print("\n[6] Exporting Sensors")

    exporter.export_sensors(
        placed_sensors
    )

    # ----------------------------------
    # Visualization
    # ----------------------------------

    print("\n[7] Generating Figures")

    viz = VisualizationManager(
        output_dir=export_cfg.plots_dir
    )

    fig = viz.terrain(
        terrain_map
    )

    viz.save(
        fig,
        "terrain.png"
    )

    fig = viz.sensors(
        terrain_map,
        placed_sensors
    )

    viz.save(
        fig,
        "sensors.png"
    )

    fig = viz.suitability(
        lb.suitability_maps
    )

    viz.save(
        fig,
        "suitability.png"
    )

    fig = viz.layers(
        lb.elevation_layer,
        lb.visibility_layer,
        lb.strategic_layer,
        lb.nfz_mask
    )

    viz.save(
        fig,
        "layers.png"
    )

    fig = viz.terrain_3d(
        height_map
    )

    viz.save(
        fig,
        "terrain_3d.png"
    )

    print("\nFigures Saved")

    # ----------------------------------
    # Summary
    # ----------------------------------

    print("\n==============================")
    print(" RUN COMPLETE ")
    print("==============================")

    print(f"Seed: {seed}")
    print(f"Sensors Placed: {len(placed_sensors)}")

    print("Outputs:")
    print("  terrain_height.csv")
    print("  terrain_type.csv")
    print("  sensor.csv")
    print("  nfz.csv")
    print("  terrain.png")
    print("  sensors.png")
    print("  suitability.png")
    print("  layers.png")
    print("  terrain_3d.png")
    print()


if __name__ == "__main__":

    main()
