"""
placement_engine.py
===================
Phase 2 — Greedy Sensor Placement Engine.

Implements the weighted greedy placement algorithm:

    For each sensor type:
      1. Take the pre-built suitability map (NFZ cells already zeroed).
      2. Flatten and argsort descending → ranked candidate list.
      3. Iterate candidates in order:
           - Skip if min Euclidean distance to already-placed sensors
             of the same type < separation threshold.
           - Otherwise place sensor here.
      4. Stop when the requested count is reached or candidates exhausted.

No optimisation algorithms (GA, ACO, MCLP) are used.
No LOS constraints are applied here.
Separation is Euclidean distance in grid cells.

Sensor counts are NOT stored in config.
They are supplied at call time via the `counts` parameter of `place()`.
"""

from __future__ import annotations

from typing import Dict, List, Optional, Tuple

import numpy as np

from config import SensorPlacementConfig, DEFAULT_CONFIG
from sensor_types import (
    SENSOR_TYPES,
    SENSOR_REGISTRY,
    PlacedSensor,
)


class PlacementEngine:
    """
    Greedy placement engine.  Stateless between calls — each call to
    place() is independent and returns a fresh list of PlacedSensor objects.

    Parameters
    ----------
    tg  : TerrainGenerator
        Live terrain object.  Used to read elevation and terrain_type
        at the chosen cell for each PlacedSensor record.
    lb  : LayerBuilder
        Pre-built layer builder carrying suitability_maps and nfz_mask.
    cfg : SensorPlacementConfig
        Master config (separation distances, cell_size_m, etc.).
    """

    def __init__(self, tg, lb, cfg: SensorPlacementConfig = DEFAULT_CONFIG):
        self.tg  = tg
        self.lb  = lb
        self.cfg = cfg
        self.rows = tg.grid_size
        self.cols = tg.grid_size

    # -----------------------------------------------------------------------
    # Public interface
    # -----------------------------------------------------------------------

    def place(self, counts: Dict[str, int]) -> List[PlacedSensor]:
        """
        Place sensors for all types and return the full placement list.

        Parameters
        ----------
        counts : dict[str, int]
            Number of sensors to place per type.
            e.g. {'radar': 6, 'visual': 8, 'infrared': 6, 'acoustic': 8}
            Supplied at runtime from main.py — not stored in config.

        Returns
        -------
        List[PlacedSensor]
            All placed sensors across all types, in placement order.
            sensor_id is globally unique and sequential (1-based).
        """
        all_placed: List[PlacedSensor] = []
        global_id = 1

        for st in SENSOR_TYPES:
            name  = st.name
            count = counts.get(name, 0)
            if count <= 0:
                continue

            placed = self._place_type(
                sensor_type=st,
                count=count,
                start_id=global_id,
            )
            all_placed.extend(placed)
            global_id += len(placed)

        return all_placed

    # -----------------------------------------------------------------------
    # Core greedy algorithm
    # -----------------------------------------------------------------------

    def _place_type(
        self,
        sensor_type,
        count: int,
        start_id: int,
    ) -> List[PlacedSensor]:
        """
        Greedy placement for a single sensor type.

        Algorithm
        ---------
        1. Retrieve suitability map for this type (NFZ cells = 0).
        2. Flatten to 1-D and argsort descending — best cells first.
        3. Walk the ranked list:
               a. Convert flat index → (row, col).
               b. Skip if suitability == 0 (NFZ or normalisation floor).
               c. Skip if too close to any already-placed sensor of same type.
               d. Place sensor; record PlacedSensor; stop when count met.

        Separation check
        ----------------
        Uses Euclidean distance in grid cells:
            d(p, q) = sqrt((p.row - q.row)^2 + (p.col - q.col)^2)
        A candidate is accepted only if d >= separation[type] for ALL
        already-placed sensors of the same type.

        Parameters
        ----------
        sensor_type : SensorType
        count       : int   — number of sensors to place
        start_id    : int   — first sensor_id to assign (globally unique)

        Returns
        -------
        List[PlacedSensor]
        """
        name       = sensor_type.name
        suit_map   = self.lb.suitability_maps[name]       # (rows, cols) float32
        sep        = self.cfg.placement.separation[name]  # minimum cell distance
        cell_size  = self.cfg.terrain.cell_size_m

        # Flatten suitability scores and rank descending
        flat_suit  = suit_map.flatten()
        ranked_idx = np.argsort(flat_suit)[::-1]          # best → worst

        placed: List[PlacedSensor] = []
        placed_coords: List[Tuple[int, int]] = []         # (row, col) fast check

        for flat_i in ranked_idx:
            if len(placed) >= count:
                break

            score = float(flat_suit[flat_i])
            if score <= 0.0:
                # Remaining candidates are NFZ-zeroed or zero suitability
                break

            row = int(flat_i // self.cols)
            col = int(flat_i  % self.cols)

            # Separation check against all already-placed sensors of this type
            if not self._passes_separation(row, col, placed_coords, sep):
                continue

            # Construct PlacedSensor record
            sensor = PlacedSensor(
                sensor_id    = start_id + len(placed),
                sensor_type  = name,
                row          = row,
                col          = col,
                elevation_m  = float(self.tg.terrain[row, col]),
                terrain_class= str(self.tg.terrain_type[row, col]),
                suitability  = score,
                _cell_size_m = cell_size,
            )
            placed.append(sensor)
            placed_coords.append((row, col))

        if len(placed) < count:
            print(
                f"  [WARNING] {name}: requested {count} sensors, "
                f"placed {len(placed)} "
                f"(grid too small, separation too large, or NFZ coverage too high)"
            )

        return placed

    # -----------------------------------------------------------------------
    # Separation helper
    # -----------------------------------------------------------------------

    @staticmethod
    def _passes_separation(
        row: int,
        col: int,
        existing: List[Tuple[int, int]],
        min_sep: float,
    ) -> bool:
        """
        Return True if (row, col) is at least min_sep cells away from
        every coordinate in `existing`.

        Uses squared-distance comparison to avoid sqrt for every check,
        converting only once: min_sep_sq = min_sep^2.
        """
        if not existing:
            return True

        min_sep_sq = min_sep ** 2
        for (er, ec) in existing:
            d_sq = (row - er) ** 2 + (col - ec) ** 2
            if d_sq < min_sep_sq:
                return False
        return True

    # -----------------------------------------------------------------------
    # Diagnostics
    # -----------------------------------------------------------------------

    def summary(self, placed: List[PlacedSensor]) -> str:
        """Return a printable placement summary grouped by sensor type."""
        lines = [
            "=" * 60,
            "  Placement Engine — Results",
            "=" * 60,
        ]

        by_type: Dict[str, List[PlacedSensor]] = {}
        for p in placed:
            by_type.setdefault(p.sensor_type, []).append(p)

        for st in SENSOR_TYPES:
            name    = st.name
            sensors = by_type.get(name, [])
            if not sensors:
                continue

            scores = [s.suitability for s in sensors]
            elevs  = [s.elevation_m for s in sensors]
            lines.append(f"\n  {st.label} ({name})  — {len(sensors)} placed")
            lines.append(
                f"    suitability : min={min(scores):.3f}  "
                f"max={max(scores):.3f}  mean={sum(scores)/len(scores):.3f}"
            )
            lines.append(
                f"    elevation   : min={min(elevs):.0f}m  "
                f"max={max(elevs):.0f}m  mean={sum(elevs)/len(elevs):.0f}m"
            )

            # Terrain class breakdown
            class_counts: Dict[str, int] = {}
            for s in sensors:
                class_counts[s.terrain_class] = \
                    class_counts.get(s.terrain_class, 0) + 1
            breakdown = "  ".join(
                f"{k}:{v}" for k, v in sorted(class_counts.items())
            )
            lines.append(f"    terrain     : {breakdown}")

            # Individual placements
            for s in sensors:
                lines.append(
                    f"      #{s.sensor_id:>3}  "
                    f"({s.row:3d},{s.col:3d})  "
                    f"elev={s.elevation_m:6.0f}m  "
                    f"{s.terrain_class:<10}  "
                    f"score={s.suitability:.3f}"
                )

        lines.append("\n" + "=" * 60)
        lines.append(f"  Total sensors placed: {len(placed)}")
        lines.append("=" * 60)
        return "\n".join(lines)


# ---------------------------------------------------------------------------
# Self-test
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import sys
    import numpy as _np

    sys.path.insert(0, ".")

    from terraingeneration import TerrainGenerator
    from config import DEFAULT_CONFIG
    from layer_builder import LayerBuilder

    # Build terrain
    seed = 42
    _np.random.seed(seed)
    tg = TerrainGenerator(
        grid_size=100, scale=40.0, octaves=6,
        persistence=0.5, lacunarity=2.0, seed=seed
    )
    tg.generate_base_terrain()
    tg.add_ridges(num_ridges=4, ridge_height=180, ridge_width=6.0)
    tg.add_valleys(num_valleys=2, valley_depth=150, valley_width=10.0)
    tg.classify_terrain()
    tg.calculate_slope()
    tg.generate_cost_map()

    # Build layers
    lb = LayerBuilder(tg, DEFAULT_CONFIG)

    # Run placement
    engine = PlacementEngine(tg, lb, DEFAULT_CONFIG)
    counts = {'radar': 6, 'visual': 8, 'infrared': 6, 'acoustic': 8}
    placed = engine.place(counts)

    print(engine.summary(placed))

    # --- Assertions ---

    # Total count
    assert len(placed) == sum(counts.values()), \
        f"Expected {sum(counts.values())} sensors, got {len(placed)}"
    print(f"\nPASS  total sensors placed = {len(placed)}")

    # IDs are unique and sequential from 1
    ids = [p.sensor_id for p in placed]
    assert ids == list(range(1, len(placed) + 1)), "sensor_ids not sequential"
    print("PASS  sensor_ids are unique and sequential")

    # No sensor placed in an NFZ cell
    for p in placed:
        assert lb.nfz_mask[p.row, p.col] == 0, \
            f"Sensor {p.sensor_id} placed inside NFZ at ({p.row},{p.col})"
    print("PASS  no sensor placed inside NFZ")

    # Separation enforced per type
    by_type: Dict[str, List] = {}
    for p in placed:
        by_type.setdefault(p.sensor_type, []).append(p)

    for stype, sensors in by_type.items():
        sep = DEFAULT_CONFIG.placement.separation[stype]
        for i, a in enumerate(sensors):
            for b in sensors[i+1:]:
                d = ((a.row - b.row)**2 + (a.col - b.col)**2) ** 0.5
                assert d >= sep, (
                    f"{stype} sensors #{a.sensor_id} and #{b.sensor_id} "
                    f"are {d:.2f} cells apart — minimum is {sep}"
                )
    print("PASS  separation constraints satisfied for all sensor types")

    # Metric coordinates correct
    for p in placed:
        assert p.x_m == p.col * DEFAULT_CONFIG.terrain.cell_size_m
        assert p.y_m == p.row * DEFAULT_CONFIG.terrain.cell_size_m
    print("PASS  metric coordinates (x_m, y_m) are correct")

    # to_dict schema
    d = placed[0].to_dict()
    for key in ('id','sensor_type','label','row','col',
                'x_m','y_m','elevation_m','terrain_class','suitability'):
        assert key in d, f"Missing key '{key}' in to_dict()"
    print("PASS  PlacedSensor.to_dict() schema complete")

    print("\nAll placement_engine.py checks passed.")