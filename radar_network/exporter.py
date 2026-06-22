"""
exporter.py
===========
Exports placed sensor data to sensor_map.json.

Each sensor entry follows this schema:
    {
      "id":            1,
      "sensor_type":   "radar",
      "label":         "Radar",
      "row":           45,
      "col":           67,
      "x_m":           6700.0,
      "y_m":           4500.0,
      "elevation_m":   823.4,
      "terrain_class": "Mountain",
      "suitability":   0.9134
    }

Metric conversion: x_m = col * cell_size_m,  y_m = row * cell_size_m
At 100 m/cell on a 100x100 grid: coverage area = 10 km x 10 km.

The top-level JSON object also includes a run metadata block:
    {
      "metadata": {
        "grid_size":      100,
        "cell_size_m":    100.0,
        "coverage_km2":   100.0,
        "total_sensors":  28,
        "active_nfzs":    5,
        "seed":           42,
        "sensor_counts":  {"radar": 6, "visual": 8, ...}
      },
      "sensors": [ ... ]
    }
"""

from __future__ import annotations

import json
import os
from typing import Dict, List

from config import SensorPlacementConfig, DEFAULT_CONFIG
from sensor_types import SENSOR_TYPES, PlacedSensor


class Exporter:
    """
    Serialises placement results to sensor_map.json.

    Parameters
    ----------
    tg  : TerrainGenerator  — provides grid_size and seed for metadata.
    lb  : LayerBuilder      — provides active NFZ count for metadata.
    cfg : SensorPlacementConfig
    """

    def __init__(self, tg, lb, cfg: SensorPlacementConfig = DEFAULT_CONFIG):
        self.tg  = tg
        self.lb  = lb
        self.cfg = cfg
        os.makedirs(os.path.dirname(cfg.export.output_file), exist_ok=True)

    def export(self, placed: List[PlacedSensor], seed: int) -> str:
        """
        Write sensor_map.json and return the output file path.

        Parameters
        ----------
        placed : list of PlacedSensor objects from PlacementEngine.
        seed   : the terrain generation seed used for this run (for metadata).
        """
        cell_m = self.cfg.export.cell_size_m
        gs     = self.tg.grid_size

        # Per-type sensor counts
        counts: Dict[str, int] = {}
        for st in SENSOR_TYPES:
            counts[st.name] = sum(1 for p in placed if p.sensor_type == st.name)

        payload = {
            "metadata": {
                "grid_size":     gs,
                "cell_size_m":   cell_m,
                "coverage_km2":  round((gs * cell_m / 1000) ** 2, 2),
                "total_sensors": len(placed),
                "active_nfzs":   len(self.lb.active_nfzs),
                "seed":          seed,
                "sensor_counts": counts,
            },
            "sensors": [p.to_dict() for p in placed],
        }

        path = self.cfg.export.output_file
        with open(path, "w", encoding="utf-8") as f:
            json.dump(payload, f, indent=2)

        return path


# ---------------------------------------------------------------------------
# Self-test
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import sys
    import numpy as _np

    sys.path.insert(0, ".")
    from terraingeneration import TerrainGenerator
    from config import DEFAULT_CONFIG, SensorPlacementConfig
    from layer_builder import LayerBuilder
    from placement_engine import PlacementEngine

    seed = 42
    _np.random.seed(seed)
    tg = TerrainGenerator(
        grid_size=100, scale=40.0, octaves=6,
        persistence=0.5, lacunarity=2.0, seed=seed,
    )
    tg.generate_base_terrain()
    tg.add_ridges(num_ridges=4, ridge_height=180, ridge_width=6.0)
    tg.add_valleys(num_valleys=2, valley_depth=150, valley_width=10.0)
    tg.classify_terrain()
    tg.calculate_slope()
    tg.generate_cost_map()

    cfg = SensorPlacementConfig()
    lb  = LayerBuilder(tg, cfg)
    engine = PlacementEngine(tg, lb, cfg)
    placed = engine.place({'radar': 6, 'visual': 8, 'infrared': 6, 'acoustic': 8})

    exporter = Exporter(tg, lb, cfg)
    path = exporter.export(placed, seed=seed)
    print(f"Exported → {path}")

    # Verify JSON structure
    with open(path) as f:
        data = json.load(f)

    assert "metadata" in data and "sensors" in data
    assert data["metadata"]["total_sensors"] == len(placed)
    assert data["metadata"]["coverage_km2"]  == 100.0
    assert len(data["sensors"])              == len(placed)

    required = {'id','sensor_type','label','row','col',
                'x_m','y_m','elevation_m','terrain_class','suitability'}
    for entry in data["sensors"]:
        assert required.issubset(entry.keys()), f"Missing keys in {entry}"

    print(f"PASS  {len(data['sensors'])} sensors, all keys present")
    print(f"PASS  coverage_km2 = {data['metadata']['coverage_km2']}")
    print(f"PASS  sensor_counts = {data['metadata']['sensor_counts']}")
    print(json.dumps(data["sensors"][0], indent=2))
    print("\nAll exporter.py checks passed.")