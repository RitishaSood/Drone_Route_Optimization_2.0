"""
terrain_generator.py
====================

Minecraft/Chunkbase-style terrain generator.

World Model:
    100 x 100 x 100

X,Y:
    0..99

Z:
    0..99

1 XY unit = 1 km
1 Z unit = 100 m

Output:
    height_map  -> z values
    terrain_map -> terrain class ids
"""

from __future__ import annotations

import random

import noise
import numpy as np
from scipy.ndimage import gaussian_filter

from config.terrain_config import TerrainConfig
from terrain.terrain_constants import *


class TerrainGenerator:

    def __init__(
        self,
        cfg: TerrainConfig
    ):

        self.cfg = cfg
        self.seed = cfg.seed

        if self.seed is not None:
            np.random.seed(self.seed)
            random.seed(self.seed)

        self.grid_size_x = cfg.grid_size_x
        self.grid_size_y = cfg.grid_size_y
        self.grid_size_z = cfg.grid_size_z

        self.height_map = np.zeros(
            (self.grid_size_x, self.grid_size_y),
            dtype=np.uint8
        )

        self.terrain_map = np.zeros(
            (self.grid_size_x, self.grid_size_y),
            dtype=np.uint8
        )

        self.water_mask = np.zeros_like(
            self.height_map,
            dtype=bool
        )

        self.forest_mask = np.zeros_like(
            self.height_map,
            dtype=bool
        )

        self.high_ground_positions = []

        self.elevation_noise = None
        self.continentalness_noise = None
        self.moisture_noise = None
        self.erosion_noise = None

    # --------------------------------------------------
    # Noise Utility
    # --------------------------------------------------

    def _noise_map(
        self,
        scale,
        octaves,
        persistence,
        lacunarity,
        seed_offset
    ):

        result = np.zeros(
            (self.grid_size_x, self.grid_size_y),
            dtype=np.float32
        )

        base_seed = 0

        if self.seed is not None:
            base_seed = int(self.seed)

        for x in range(self.grid_size_x):
            for y in range(self.grid_size_y):

                result[x, y] = noise.pnoise2(
                    x / scale,
                    y / scale,
                    octaves=octaves,
                    persistence=persistence,
                    lacunarity=lacunarity,
                    repeatx=999999,
                    repeaty=999999,
                    base=base_seed + seed_offset
                )

        result -= result.min()

        max_value = result.max()

        if max_value > 0:
            result /= max_value

        return result

    # --------------------------------------------------
    # Minecraft-like Noise Fields
    # --------------------------------------------------

    def generate_noise_maps(
        self
    ):

        # Broad landmass pattern
        self.continentalness_noise = self._noise_map(
            scale=55.0,
            octaves=4,
            persistence=0.5,
            lacunarity=2.0,
            seed_offset=10
        )

        # Base elevation detail
        self.elevation_noise = self._noise_map(
            scale=35.0,
            octaves=5,
            persistence=0.45,
            lacunarity=2.1,
            seed_offset=20
        )

        # Forest / dry land control
        self.moisture_noise = self._noise_map(
            scale=42.0,
            octaves=4,
            persistence=0.55,
            lacunarity=2.0,
            seed_offset=30
        )

        # Breaks terrain into hills/valleys
        self.erosion_noise = self._noise_map(
            scale=28.0,
            octaves=4,
            persistence=0.5,
            lacunarity=2.2,
            seed_offset=40
        )

    # --------------------------------------------------
    # Height Generation
    # --------------------------------------------------

    def generate_heightmap(
        self
    ):

        elevation = self.elevation_noise
        continentalness = self.continentalness_noise
        erosion = self.erosion_noise

        # Minecraft-like combined terrain signal
        combined = (
            0.55 * elevation +
            0.35 * continentalness +
            0.10 * (1.0 - erosion)
        )

        # Smooth broad terrain
        combined = gaussian_filter(
            combined,
            sigma=1.2
        )

        height = np.zeros_like(
            combined,
            dtype=np.float32
        )

        for x in range(self.grid_size_x):
            for y in range(self.grid_size_y):

                c = continentalness[x, y]
                e = combined[x, y]

                if c < 0.28:
                    # water
                    height[x, y] = 0

                elif e < 0.30:
                    # lowlands / valleys
                    height[x, y] = 2 + e * 12

                elif e < 0.55:
                    # plains
                    height[x, y] = 5 + e * 15

                elif e < 0.75:
                    # hills
                    height[x, y] = 10 + e * 22

                else:
                    # mountains, capped for UAV placement suitability
                    height[x, y] = 18 + e * 30

        height = gaussian_filter(
            height,
            sigma=1.0
        )

        height = np.clip(
            height,
            0,
            45
        )

        self.height_map = height.astype(
            np.uint8
        )

    # --------------------------------------------------
    # Terrain Classification
    # --------------------------------------------------

    def classify_terrain(
        self
    ):

        self.terrain_map.fill(
            PLAIN
        )

        self.water_mask.fill(
            False
        )

        self.forest_mask.fill(
            False
        )

        for x in range(self.grid_size_x):
            for y in range(self.grid_size_y):

                z = int(
                    self.height_map[x, y]
                )

                continentalness = self.continentalness_noise[x, y]
                moisture = self.moisture_noise[x, y]
                elevation = self.elevation_noise[x, y]
                erosion = self.erosion_noise[x, y]

                if continentalness < 0.28:

                    self.terrain_map[x, y] = WATER
                    self.water_mask[x, y] = True
                    self.height_map[x, y] = 0

                elif z >= 26 and elevation > 0.60:

                    self.terrain_map[x, y] = MOUNTAIN

                elif z >= 15:

                    self.terrain_map[x, y] = HILL

                elif z <= 5 and erosion < 0.45:

                    self.terrain_map[x, y] = VALLEY

                elif moisture > 0.55 and z < 18:

                    self.terrain_map[x, y] = FOREST
                    self.forest_mask[x, y] = True

                else:

                    self.terrain_map[x, y] = PLAIN

        self.clean_small_artifacts()
        self.find_high_ground()

    # --------------------------------------------------
    # Remove tiny noisy patches
    # --------------------------------------------------

    def clean_small_artifacts(
        self
    ):

        cleaned = self.terrain_map.copy()

        for x in range(1, self.grid_size_x - 1):
            for y in range(1, self.grid_size_y - 1):

                local = self.terrain_map[
                    x - 1:x + 2,
                    y - 1:y + 2
                ]

                values, counts = np.unique(
                    local,
                    return_counts=True
                )

                majority = values[
                    np.argmax(counts)
                ]

                if counts.max() >= 6:
                    cleaned[x, y] = majority

        self.terrain_map = cleaned

        self.water_mask = self.terrain_map == WATER
        self.forest_mask = self.terrain_map == FOREST

    # --------------------------------------------------
    # Strategic Peaks
    # --------------------------------------------------

    def find_high_ground(
        self
    ):

        peaks = []

        for x in range(2, self.grid_size_x - 2):
            for y in range(2, self.grid_size_y - 2):

                if self.terrain_map[x, y] != MOUNTAIN:
                    continue

                local = self.height_map[
                    x - 2:x + 3,
                    y - 2:y + 3
                ]

                if (
                    self.height_map[x, y] == np.max(local)
                    and
                    self.height_map[x, y] >= 25
                ):

                    peaks.append(
                        (
                            x,
                            y,
                            int(self.height_map[x, y])
                        )
                    )

        peaks.sort(
            key=lambda p: p[2],
            reverse=True
        )

        selected = []

        min_distance = 10

        for px, py, h in peaks:

            valid = True

            for sx, sy in selected:

                if np.hypot(px - sx, py - sy) < min_distance:
                    valid = False
                    break

            if valid:
                selected.append(
                    (
                        px,
                        py
                    )
                )

            if len(selected) >= 12:
                break

        self.high_ground_positions = selected

    # --------------------------------------------------
    # Full Generation
    # --------------------------------------------------

    def generate(
        self
    ):

        print("[TG] generating climate/noise maps", flush=True)
        self.generate_noise_maps()

        print("[TG] generating heightmap", flush=True)
        self.generate_heightmap()

        print("[TG] classifying terrain", flush=True)
        self.classify_terrain()

        print("[TG] done", flush=True)

        return (
            self.height_map,
            self.terrain_map
        )