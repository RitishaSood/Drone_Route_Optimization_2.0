"""
layer_builder.py
================
Phase 2 — Layer construction and suitability map generation.

Consumes terraingeneration.py outputs directly:
    tg.terrain              → elevation matrix   [0–1000 m]
    tg.terrain_type         → terrain class per cell (string)
    tg.slope_map            → slope gradient matrix
    tg.high_ground_positions→ list of (row, col) strategic outposts
    tg.grid_size            → authoritative grid dimension
    tg.classes              → authoritative terrain class names

Builds four normalised input layers [0, 1]:
    elevation_layer     — normalised terrain height
    strategic_layer     — Gaussian influence from high-ground outposts
    visibility_layer    — terrain-class heuristic (Phase 2 approximation)
    nfz_mask            — binary no-fly zone mask (1 = restricted)

Then computes one suitability map [0, 1] per sensor type using the
weighted formula from SuitabilityWeights, with NFZ cells zeroed out.
"""

from __future__ import annotations

import random
from typing import Dict, List, Optional, Tuple

import numpy as np

from config import SensorPlacementConfig, DEFAULT_CONFIG
from sensor_types import SENSOR_TYPES, SensorType


# ---------------------------------------------------------------------------
# LayerBuilder
# ---------------------------------------------------------------------------

class LayerBuilder:
    """
    Builds all input layers and suitability maps from a live
    TerrainGenerator object.

    Parameters
    ----------
    tg  : TerrainGenerator
        Fully initialised terrain generator (generate_base_terrain,
        classify_terrain, and calculate_slope must already have been
        called by main.py before passing tg here).
    cfg : SensorPlacementConfig
        Master config.  Defaults to DEFAULT_CONFIG.

    Attributes (populated after build())
    -------------------------------------
    elevation_layer  : np.ndarray (rows, cols) float32  [0, 1]
    strategic_layer  : np.ndarray (rows, cols) float32  [0, 1]
    visibility_layer : np.ndarray (rows, cols) float32  [0, 1]
    nfz_mask         : np.ndarray (rows, cols) uint8    {0, 1}
    active_nfzs      : list of (row, col, radius) — NFZs selected this run
    suitability_maps : dict[str, np.ndarray]  one [0,1] map per sensor type
    """

    def __init__(self, tg, cfg: SensorPlacementConfig = DEFAULT_CONFIG):
        self.tg  = tg
        self.cfg = cfg

        # Read authoritative dimensions from the terrain object
        self.rows = tg.grid_size
        self.cols = tg.grid_size

        # Input layers
        self.elevation_layer  = np.zeros((self.rows, self.cols), dtype=np.float32)
        self.strategic_layer  = np.zeros((self.rows, self.cols), dtype=np.float32)
        self.visibility_layer = np.zeros((self.rows, self.cols), dtype=np.float32)
        self.nfz_mask         = np.zeros((self.rows, self.cols), dtype=np.uint8)
        self.active_nfzs: List[Tuple[int, int, int]] = []

        # Output: one suitability map per sensor type
        self.suitability_maps: Dict[str, np.ndarray] = {}

        # Build everything
        self._validate_terrain_classes()
        self.build()

    # -----------------------------------------------------------------------
    # Public interface
    # -----------------------------------------------------------------------

    def build(self) -> None:
        """
        Build all layers and suitability maps in dependency order.
        Can be called again if tg is updated (e.g. in a re-run).
        """
        self._build_elevation_layer()
        self._build_strategic_layer()
        self._build_visibility_layer()
        self._build_nfz_mask()
        self._build_suitability_maps()

    # -----------------------------------------------------------------------
    # Validation
    # -----------------------------------------------------------------------

    def _validate_terrain_classes(self) -> None:
        """
        Check that every key in visibility_scores exists in tg.classes.
        tg.classes is the single source of truth for terrain class names.
        Raises ValueError on first mismatch so errors surface early.
        """
        tg_classes = set(self.tg.classes)
        cfg_keys   = set(self.cfg.layers.visibility_scores.keys())
        unknown    = cfg_keys - tg_classes
        if unknown:
            raise ValueError(
                f"visibility_scores contains keys not found in tg.classes: "
                f"{unknown}. tg.classes = {tg_classes}"
            )

    # -----------------------------------------------------------------------
    # Layer builders
    # -----------------------------------------------------------------------

    def _normalise(self, arr: np.ndarray) -> np.ndarray:
        """Linearly normalise array to [0, 1]. Returns zeros if constant."""
        mn, mx = arr.min(), arr.max()
        if mx - mn < 1e-10:
            return np.zeros_like(arr, dtype=np.float32)
        return ((arr - mn) / (mx - mn)).astype(np.float32)

    def _build_elevation_layer(self) -> None:
        """
        Normalise tg.terrain (elevation in metres, 0–1000) to [0, 1].

        Higher values → more suitable for radar and visual sensors.
        Acoustic sensors will use (1 − elevation_layer) internally.
        """
        self.elevation_layer = self._normalise(self.tg.terrain)

    def _build_strategic_layer(self) -> None:
        """
        Build a strategic importance map from tg.high_ground_positions.

        For each outpost p at (pr, pc), compute a Gaussian influence field:

            G_p(r, c) = exp(−((r−pr)² + (c−pc)²) / (2 × σ²))

        Sum all fields, then normalise to [0, 1].

        If no high-ground positions exist (flat terrain with no peaks
        above 850 m), the layer defaults to uniform 0.0 — the placement
        engine will then rely solely on elevation and visibility.
        """
        sigma = self.cfg.layers.strategic_sigma
        positions = self.tg.high_ground_positions

        if not positions:
            # No strategic outposts identified — layer stays zero
            self.strategic_layer = np.zeros(
                (self.rows, self.cols), dtype=np.float32
            )
            return

        # Vectorised coordinate grids
        row_idx, col_idx = np.meshgrid(
            np.arange(self.rows),
            np.arange(self.cols),
            indexing='ij'           # shape (rows, cols)
        )

        influence = np.zeros((self.rows, self.cols), dtype=np.float64)
        sigma_sq  = sigma ** 2

        for (pr, pc) in positions:
            d_sq      = (row_idx - pr) ** 2 + (col_idx - pc) ** 2
            influence += np.exp(-d_sq / (2.0 * sigma_sq))

        self.strategic_layer = self._normalise(influence)

    def _build_visibility_layer(self) -> None:
        """
        Build a visibility heuristic map from tg.terrain_type.

        Phase 2 approximation — NOT a LOS or viewshed calculation.
        Each cell receives the heuristic score for its terrain class
        from cfg.layers.visibility_scores, then the map is normalised.

        Score mapping (from config):
            Mountain → 1.00   Highland → 0.85   Hill → 0.60
            Plain    → 0.40   Valley   → 0.15

        Future phases will replace this with true LOS/viewshed analysis.
        The normalised [0, 1] output contract will remain unchanged.
        """
        scores    = self.cfg.layers.visibility_scores
        raw       = np.zeros((self.rows, self.cols), dtype=np.float64)

        # Map each terrain class label to its heuristic score.
        # tg.terrain_type is a (rows, cols) array of string labels.
        for class_name, score in scores.items():
            mask     = (self.tg.terrain_type == class_name)
            raw[mask] = score

        self.visibility_layer = self._normalise(raw)

    def _build_nfz_mask(self) -> None:
        """
        Select a random subset of NFZ candidates and paint circular
        exclusion zones onto nfz_mask.

        nfz_mask[r, c] = 1  →  cell is restricted (no sensor placement)
        nfz_mask[r, c] = 0  →  cell is available

        Random selection uses cfg.nfz.nfz_random_seed if set, giving
        reproducible NFZ layouts when needed for comparison runs.
        """
        nfz_cfg = self.cfg.nfz

        # Seed the random state for NFZ selection only
        rng = random.Random(nfz_cfg.nfz_random_seed)
        k   = min(nfz_cfg.num_active_nfz, len(nfz_cfg.nfz_library))
        self.active_nfzs = rng.sample(nfz_cfg.nfz_library, k)

        self.nfz_mask[:] = 0

        # Vectorised distance check for each active NFZ
        row_idx, col_idx = np.meshgrid(
            np.arange(self.rows),
            np.arange(self.cols),
            indexing='ij'
        )

        for (nr, nc, radius) in self.active_nfzs:
            d_sq = (row_idx - nr) ** 2 + (col_idx - nc) ** 2
            self.nfz_mask[d_sq <= radius ** 2] = 1

    def _build_suitability_maps(self) -> None:
        """
        Compute one suitability map per sensor type.

        Formula for radar / visual / infrared:
            S = w_elev * elevation_layer
              + w_vis  * visibility_layer
              + w_strat* strategic_layer

        Formula for acoustic (invert_elevation=True):
            S = w_elev * (1 − elevation_layer)
              + w_vis  * visibility_layer
              + w_strat* strategic_layer

        After weighting:
          1. Normalise S to [0, 1] across the full grid.
          2. Zero out NFZ cells (nfz_mask == 1).

        NFZ zeroing happens AFTER normalisation so that NFZ regions do
        not affect the relative ranking of available cells.
        """
        nfz_bool = self.nfz_mask.astype(bool)

        for st in SENSOR_TYPES:
            weights = getattr(self.cfg.weights, st.weight_key)

            w_elev  = weights['elevation']
            w_vis   = weights['visibility']
            w_strat = weights['strategic']

            # Apply elevation inversion for acoustic sensors
            elev = (1.0 - self.elevation_layer) if st.invert_elevation \
                   else self.elevation_layer

            raw = (
                w_elev  * elev                  +
                w_vis   * self.visibility_layer  +
                w_strat * self.strategic_layer
            )

            # Normalise to [0, 1]
            suit = self._normalise(raw)

            # Zero out NFZ cells so the engine never selects them
            suit[nfz_bool] = 0.0

            self.suitability_maps[st.name] = suit

    # -----------------------------------------------------------------------
    # Diagnostics
    # -----------------------------------------------------------------------

    def summary(self) -> str:
        """Return a printable statistics summary of all built layers."""
        lines = [
            "=" * 56,
            "  LayerBuilder Summary",
            "=" * 56,
        ]

        for name, arr in [
            ("elevation",  self.elevation_layer),
            ("strategic",  self.strategic_layer),
            ("visibility", self.visibility_layer),
        ]:
            lines.append(
                f"  {name:<12} min={arr.min():.3f}  max={arr.max():.3f}"
                f"  mean={arr.mean():.3f}  std={arr.std():.3f}"
            )

        nfz_cells = int(self.nfz_mask.sum())
        total     = self.rows * self.cols
        lines.append(
            f"  nfz_mask     restricted={nfz_cells} cells "
            f"({100*nfz_cells/total:.1f}% of grid)"
        )
        lines.append(f"  active NFZs  {self.active_nfzs}")
        lines.append("")
        lines.append(f"  Suitability maps ({len(self.suitability_maps)} types):")

        for stype, arr in self.suitability_maps.items():
            available = arr[self.nfz_mask == 0]
            lines.append(
                f"    {stype:<10} max={arr.max():.3f}  "
                f"mean(avail)={available.mean():.3f}"
            )

        lines.append("=" * 56)
        return "\n".join(lines)


# ---------------------------------------------------------------------------
# Self-test
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import sys
    import random as _random
    sys.path.insert(0, ".")

    from terraingeneration import TerrainGenerator

    print("Building terrain...")
    seed = 42
    import numpy as _np
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
    print(f"  high_ground_positions: {tg.high_ground_positions}")

    print("Building layers...")
    from config import DEFAULT_CONFIG
    lb = LayerBuilder(tg, DEFAULT_CONFIG)

    print(lb.summary())

    # Range checks
    for name, arr in [
        ("elevation",  lb.elevation_layer),
        ("strategic",  lb.strategic_layer),
        ("visibility", lb.visibility_layer),
    ]:
        assert arr.min() >= 0.0, f"{name} below 0"
        assert arr.max() <= 1.0, f"{name} above 1"
        print(f"PASS  {name}_layer in [0,1]")

    # NFZ mask is binary
    assert set(lb.nfz_mask.flatten().tolist()).issubset({0, 1})
    print("PASS  nfz_mask is binary {0,1}")

    # Suitability maps: 4 types, in [0,1], NFZ cells are 0
    assert len(lb.suitability_maps) == 4
    for stype, arr in lb.suitability_maps.items():
        assert arr.min() >= 0.0 and arr.max() <= 1.0, \
            f"suitability[{stype}] out of [0,1]"
        # NFZ cells must be 0
        nfz_vals = arr[lb.nfz_mask == 1]
        assert nfz_vals.max() == 0.0, \
            f"NFZ cells in {stype} suitability map are non-zero"
    print("PASS  all 4 suitability maps in [0,1] with NFZ cells zeroed")

    # Acoustic elevation inversion: acoustic suitability should be
    # higher in lower-elevation areas than radar suitability
    low_elev_mask  = lb.elevation_layer < 0.2
    if low_elev_mask.sum() > 10:
        acoustic_mean = lb.suitability_maps['acoustic'][low_elev_mask].mean()
        radar_mean    = lb.suitability_maps['radar'][low_elev_mask].mean()
        print(f"  Low-elev acoustic mean={acoustic_mean:.3f}  "
              f"radar mean={radar_mean:.3f}  "
              f"(acoustic should favour low elevation)")

    print("\nAll layer_builder.py checks passed.")