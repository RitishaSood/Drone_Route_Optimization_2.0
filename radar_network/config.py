"""
config.py
=========
Placement-system configuration for the UAV Sensor Placement System.

This file owns ONLY placement decisions.
Terrain generation is owned entirely by terraingeneration.py.

Phase 2 Pipeline
----------------
  terraingeneration.py  →  tg.terrain / tg.terrain_type /
                            tg.slope_map / tg.high_ground_positions
        ↓
  LayerBuilder    (strategic · visibility · NFZ · elevation layers)
        ↓
  SuitabilityMap  (weighted combination per sensor type)
        ↓
  PlacementEngine (greedy, separation-constrained)
        ↓
  Visualizer + Exporter  →  sensor_map.json
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import List, Optional, Tuple


# ---------------------------------------------------------------------------
# Terrain interface — consumer side only
# ---------------------------------------------------------------------------

@dataclass
class TerrainConfig:
    """
    Placement-system knowledge about the terrain team's grid.

    grid_size and terrain_classes are intentionally NOT stored here.
    Both are read directly from the live TerrainGenerator object
    (tg.grid_size and tg.classes) at runtime, keeping the terrain
    team as the single source of truth.

    cell_size_m is kept here because it is a placement/export concern,
    not a terrain generation concern.
    """
    # Physical scale used by the exporter for metric coordinate conversion.
    # x_m = col * cell_size_m,  y_m = row * cell_size_m
    cell_size_m: float = 100.0   # 1 cell = 100 m  →  10 km × 10 km grid


# ---------------------------------------------------------------------------
# Layer builder
# ---------------------------------------------------------------------------

@dataclass
class LayerConfig:
    """
    Parameters for the three placement input layers.

    Strategic layer
    ---------------
    Built from tg.high_ground_positions (changes every terrain run).
    Each outpost p becomes a Gaussian influence zone:
        G_p(r, c) = exp(-d(r,c,p)^2 / (2 * strategic_sigma^2))
    All zones are summed and normalised to [0, 1].

    Visibility layer  (Phase 2 heuristic — not LOS/viewshed)
    ---------------------------------------------------------
    Maps tg.terrain_type labels to fixed scores, then normalises.
    Keys in visibility_scores must match values present in tg.classes.
    No duplicate class list is stored here; tg.classes is authoritative.
    Future phases will replace this with true viewshed analysis.
    """
    # Gaussian influence radius around each strategic outpost (grid cells).
    # 10 cells ≈ 1 km at 100 m/cell.
    strategic_sigma: float = 10.0

    # Heuristic visibility score per terrain class.
    # Keys are validated against tg.classes at runtime in LayerBuilder.
    visibility_scores: dict = field(default_factory=lambda: {
        'Mountain': 1.00,
        'Highland': 0.85,
        'Hill':     0.60,
        'Plain':    0.40,
        'Valley':   0.15,
    })


# ---------------------------------------------------------------------------
# No-Fly Zones
# ---------------------------------------------------------------------------

@dataclass
class NFZConfig:
    """
    NFZ candidate library with per-run random activation.

    Behaviour:
      - nfz_library defines all possible NFZ regions.
      - Each run randomly selects num_active_nfz zones from the library.
      - Selected zones are converted to a binary mask (1=restricted).
      - The selection is fixed for the duration of that run.
      - nfz_random_seed=None → random every run.
      - nfz_random_seed=<int> → deterministic (for debugging / comparison).

    Each entry: (row, col, radius_cells)
    """
    nfz_library: List[Tuple[int, int, int]] = field(default_factory=lambda: [
        (20, 20,  6),   # NFZ-01  NW quadrant
        (50, 50,  8),   # NFZ-02  central
        (75, 30,  5),   # NFZ-03  SW region
        (15, 70,  7),   # NFZ-04  NE region
        (85, 80,  6),   # NFZ-05  SE corner
        (40, 10,  5),   # NFZ-06  west flank
        (30, 85,  6),   # NFZ-07  east flank
        (60, 65,  7),   # NFZ-08  south-central
        (10, 45,  4),   # NFZ-09  north-central
        (90, 50,  5),   # NFZ-10  south-central
        (55, 20,  6),   # NFZ-11  west-central
        (45, 75,  5),   # NFZ-12  east-central
    ])
    num_active_nfz:   int           = 5
    nfz_random_seed:  Optional[int] = None   # None = random each run


# ---------------------------------------------------------------------------
# Suitability weights
# ---------------------------------------------------------------------------

@dataclass
class SuitabilityWeights:
    """
    Per-sensor-type layer weights.

    Formula (radar / visual / infrared):
        S = w_elevation * elev + w_visibility * vis + w_strategic * strat

    Acoustic uses inverted elevation (lower = less wind noise = better SNR):
        S = w_elevation * (1 - elev) + w_visibility * vis + w_strategic * strat

    Weights per sensor type must sum to 1.0 (enforced by validate()).

    Rationale:
        Radar     — elevation-heavy: altitude dominates radar horizon.
        Visual    — visibility-heavy: cameras need unobstructed sightlines.
        Infrared  — strategic-heavy: IR thermal contrast best at outposts.
        Acoustic  — strategic + inverted-elevation: lower terrain, less noise.
    """
    radar: dict = field(default_factory=lambda: {
        'elevation': 0.40, 'visibility': 0.35, 'strategic': 0.25,
    })
    visual: dict = field(default_factory=lambda: {
        'elevation': 0.20, 'visibility': 0.50, 'strategic': 0.30,
    })
    infrared: dict = field(default_factory=lambda: {
        'elevation': 0.35, 'visibility': 0.20, 'strategic': 0.45,
    })
    acoustic: dict = field(default_factory=lambda: {
        'elevation': 0.35, 'visibility': 0.15, 'strategic': 0.50,
    })


# ---------------------------------------------------------------------------
# Placement engine
# ---------------------------------------------------------------------------

@dataclass
class PlacementConfig:
    """
    Greedy placement engine parameters.

    Sensor counts are NOT stored here — they come from runtime user
    input in main.py and are passed directly into the placement engine.

    separation  : minimum Euclidean cell-distance between same-type sensors.
    markers     : matplotlib marker codes for visualisation overlay.
    colors      : hex colours per sensor type.
    marker_size : scatter plot marker area (matplotlib s= parameter).
    """
    separation: dict = field(default_factory=lambda: {
        'radar': 8, 'visual': 5, 'infrared': 5, 'acoustic': 5,
    })
    markers: dict = field(default_factory=lambda: {
        'radar': '^', 'visual': 'D', 'infrared': 's', 'acoustic': 'o',
    })
    colors: dict = field(default_factory=lambda: {
        'radar':    '#FF4444',
        'visual':   '#44FF44',
        'infrared': '#FF8800',
        'acoustic': '#4488FF',
    })
    marker_size: int = 120


# ---------------------------------------------------------------------------
# Visualisation
# ---------------------------------------------------------------------------

@dataclass
class VizConfig:
    """Matplotlib output settings. Follows terrain team's plotting style."""
    figure_dpi: int  = 150
    output_dir: str  = "outputs"
    show_plots: bool = True


# ---------------------------------------------------------------------------
# Export
# ---------------------------------------------------------------------------

@dataclass
class ExportConfig:
    """JSON export settings."""
    output_file: str   = "outputs/sensor_map.json"
    cell_size_m: float = 100.0   # must match TerrainConfig.cell_size_m


# ---------------------------------------------------------------------------
# Master config + validation
# ---------------------------------------------------------------------------

@dataclass
class SensorPlacementConfig:
    """
    Aggregated configuration object.

    Usage:
        from config import DEFAULT_CONFIG
        cfg = DEFAULT_CONFIG
        cfg.validate()
    """
    terrain:   TerrainConfig      = field(default_factory=TerrainConfig)
    layers:    LayerConfig        = field(default_factory=LayerConfig)
    nfz:       NFZConfig          = field(default_factory=NFZConfig)
    weights:   SuitabilityWeights = field(default_factory=SuitabilityWeights)
    placement: PlacementConfig    = field(default_factory=PlacementConfig)
    viz:       VizConfig          = field(default_factory=VizConfig)
    export:    ExportConfig       = field(default_factory=ExportConfig)

    def validate(self) -> None:
        """
        Lightweight config sanity check.  Call once at startup in main.py.
        Raises ValueError with a clear message on the first problem found.
        """
        # Strategic sigma
        if self.layers.strategic_sigma <= 0:
            raise ValueError(
                f"layers.strategic_sigma must be > 0, got {self.layers.strategic_sigma}"
            )

        # NFZ count feasibility
        lib_size = len(self.nfz.nfz_library)
        if self.nfz.num_active_nfz > lib_size:
            raise ValueError(
                f"nfz.num_active_nfz ({self.nfz.num_active_nfz}) exceeds "
                f"nfz_library size ({lib_size})"
            )

        # Suitability weight sums
        sensor_weights = {
            'radar':    self.weights.radar,
            'visual':   self.weights.visual,
            'infrared': self.weights.infrared,
            'acoustic': self.weights.acoustic,
        }
        for sensor, w in sensor_weights.items():
            total = sum(w.values())
            if not math.isclose(total, 1.0, abs_tol=1e-6):
                raise ValueError(
                    f"weights.{sensor} must sum to 1.0, got {total:.6f}"
                )

        # Separation distances
        for sensor, sep in self.placement.separation.items():
            if sep <= 0:
                raise ValueError(
                    f"placement.separation['{sensor}'] must be > 0, got {sep}"
                )

        # cell_size_m consistency
        if self.terrain.cell_size_m != self.export.cell_size_m:
            raise ValueError(
                f"terrain.cell_size_m ({self.terrain.cell_size_m}) and "
                f"export.cell_size_m ({self.export.cell_size_m}) must match"
            )


DEFAULT_CONFIG = SensorPlacementConfig()