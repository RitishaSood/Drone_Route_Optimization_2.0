"""
placement/layer_builder.py
==========================

Builds all placement input layers:

1. Elevation Layer
2. Strategic Layer
3. Visibility Layer
4. NFZ Mask

Then generates suitability maps for:

- Radar
- Infrared
- Visual
- Acoustic

LayerBuilder acts as the bridge between:

TerrainGenerator
        ↓
PlacementEngine

The placement engine should only interact with LayerBuilder.
"""

from __future__ import annotations

import numpy as np

from placement.strategic import StrategicLayerGenerator
from placement.visibility import VisibilityLayerGenerator
from placement.nfz import NFZLoader
from placement.suitability import SuitabilityBuilder


class LayerBuilder:

    def __init__(
        self,
        terrain_generator,
        nfz_file
    ):

        self.tg = terrain_generator

        self.height_map = terrain_generator.height_map

        self.terrain_map = terrain_generator.terrain_map

        self.high_ground_positions = (
            terrain_generator.high_ground_positions
        )

        self.grid_size = self.height_map.shape[0]

        # --------------------------------------------------
        # Elevation Layer
        # Normalized:
        # 0.0 = sea level
        # 1.0 = highest possible terrain
        # --------------------------------------------------

        self.elevation_layer = (
            self.height_map.astype(np.float32) / 99.0
        )

        # --------------------------------------------------
        # Strategic Layer
        # --------------------------------------------------

        self.strategic_layer = (
            StrategicLayerGenerator.build(
                self.grid_size,
                self.high_ground_positions
            )
        )

        # --------------------------------------------------
        # Visibility Layer
        # --------------------------------------------------

        self.visibility_layer = (
            VisibilityLayerGenerator.build(
                self.terrain_map
            )
        )

        # --------------------------------------------------
        # NFZ Mask
        # --------------------------------------------------

        self.nfz_mask = NFZLoader.build_mask(
            nfz_file,
            self.grid_size
        )

        # --------------------------------------------------
        # Validation
        # --------------------------------------------------

        assert self.elevation_layer.shape == (
            self.grid_size,
            self.grid_size
        )

        assert self.visibility_layer.shape == (
            self.grid_size,
            self.grid_size
        )

        assert self.strategic_layer.shape == (
            self.grid_size,
            self.grid_size
        )

        assert self.nfz_mask.shape == (
            self.grid_size,
            self.grid_size
        )

        # --------------------------------------------------
        # Suitability Maps
        # --------------------------------------------------

        self.suitability_maps = {

            "radar":
                SuitabilityBuilder.build_radar(
                    self.elevation_layer,
                    self.visibility_layer,
                    self.strategic_layer
                ),

            "infrared":
                SuitabilityBuilder.build_ir(
                    self.elevation_layer,
                    self.visibility_layer,
                    self.strategic_layer
                ),

            "visual":
                SuitabilityBuilder.build_visual(
                    self.elevation_layer,
                    self.visibility_layer,
                    self.strategic_layer
                ),

            "acoustic":
                SuitabilityBuilder.build_acoustic(
                    self.elevation_layer,
                    self.visibility_layer,
                    self.strategic_layer
                )
        }

        # --------------------------------------------------
        # Diagnostics
        # --------------------------------------------------

        print(
            f"[LAYER] Grid Size: "
            f"{self.grid_size} x {self.grid_size}"
        )

        print(
            f"[LAYER] Strategic Peaks: "
            f"{len(self.high_ground_positions)}"
        )

        print(
            f"[LAYER] NFZ Cells: "
            f"{int(self.nfz_mask.sum())}"
        )

    # ------------------------------------------------------
    # Helper Functions
    # ------------------------------------------------------

    def get_suitability(
        self,
        sensor_type
    ):

        return self.suitability_maps[sensor_type]

    def is_restricted(
        self,
        x,
        y
    ):

        return self.nfz_mask[x, y] == 1