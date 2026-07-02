from __future__ import annotations

import numpy as np

from placement.greedy_sensor_placement import GreedySensorPlacement
from placement.sensor_types import SENSOR_TYPES
from placement.placed_sensor import PlacedSensor
from placement.nfz import NFZLoader

from terrain.terrain_constants import (
    FOREST,
    HILL,
    MOUNTAIN,
    PLAIN,
    VALLEY,
    WATER,
)


class PlacementEngine:

    def __init__(
        self,
        terrain_generator,
        layer_builder,
        placement_config
    ):

        self.tg = terrain_generator
        self.lb = layer_builder
        self.cfg = placement_config

        self.height_map = terrain_generator.height_map
        self.terrain_map = terrain_generator.terrain_map

        self.nfz_mask = layer_builder.nfz_mask
        self.suitability_maps = layer_builder.suitability_maps

    # --------------------------------------------------
    # Public API
    # --------------------------------------------------

    def place(
        self,
        sensor_counts: dict
    ) -> list[PlacedSensor]:

        placed = []

        next_id = 1

        for sensor_def in SENSOR_TYPES:

            count = sensor_counts.get(
                sensor_def.name,
                0
            )

            suitability = self.suitability_maps[
                sensor_def.name
            ]

            sensor_list = self._place_sensor_type(
                sensor_def.name,
                sensor_def.label,
                count,
                suitability,
                placed,
                next_id
            )

            placed.extend(
                sensor_list
            )

            next_id += len(
                sensor_list
            )

        return placed

    # --------------------------------------------------
    # Per sensor placement
    # --------------------------------------------------

    def _place_sensor_type(
        self,
        sensor_type,
        label,
        count,
        suitability,
        existing_sensors,
        starting_id
    ):

        placed = []

        if count <= 0:
            return placed

        sensor_id = starting_id
        grid_size = self.height_map.shape[0]
        min_distance = self._get_separation(
            sensor_type
        )

        # Placement maps are exported/consumed as top-left row matrices.
        # The terrain generator keeps arrays as [x, y], so build matching
        # top-left views before using bottom-left world coordinates.
        suitability_top_left = suitability.T[::-1]
        terrain_top_left = self.terrain_map.T[::-1]

        allowed_terrain_ids = self._allowed_terrain_ids(
            sensor_type
        )

        def is_valid_candidate(x, y):
            return self._valid_location(
                x,
                y,
                sensor_type,
                existing_sensors + placed
            )

        existing_coords = [
            (
                sensor.x,
                sensor.y
            )
            for sensor in existing_sensors
        ]

        placer = GreedySensorPlacement(
            grid_size=grid_size,
            min_distance=min_distance,
            seed=getattr(self.tg, "seed", 42)
        )

        selected_coords = placer.place_sensors(
            suitability_map=suitability_top_left,
            terrain_type_map=terrain_top_left,
            total_sensors=count,
            allowed_terrain_ids=allowed_terrain_ids,
            existing_coords=existing_coords,
            is_valid_location=is_valid_candidate,
            debug_label=sensor_type
        )

        for x, y in selected_coords:
            sensor = PlacedSensor(
                sensor_id=sensor_id,
                sensor_type=sensor_type,
                label=f"{label}_{len(placed) + 1}",
                x=x,
                y=y,
                z=int(
                    self.height_map[x, y]
                ),
                terrain_class=int(
                    self.terrain_map[x, y]
                ),
                suitability_score=float(
                    suitability[x, y]
                )
            )

            placed.append(
                sensor
            )

            sensor_id += 1

        return placed

    # --------------------------------------------------
    # Location validation
    # --------------------------------------------------

    def _valid_location(
        self,
        x,
        y,
        sensor_type,
        existing_sensors
    ):

        # Bounds check
        if (
            x < 0 or
            y < 0 or
            x >= self.height_map.shape[0] or
            y >= self.height_map.shape[1]
        ):
            return False

        # Water forbidden unless explicitly enabled in placement config.
        if self.terrain_map[x, y] == WATER:
            if not getattr(self.cfg, "allow_water", False):
                return False

        # Sea-level forbidden as extra safety
        if self.height_map[x, y] <= 0:
            return False

        # NFZ forbidden
        if NFZLoader.is_inside_nfz(
            x,
            y,
            self.nfz_mask
        ):
            return False

        same_type_separation = self._get_separation(
            sensor_type
        )

        # Keep different sensor types apart too
        cross_type_separation = 8

        for sensor in existing_sensors:

            dx = sensor.x - x
            dy = sensor.y - y

            dist = np.hypot(
                dx,
                dy
            )

            if sensor.sensor_type == sensor_type:
                required_separation = same_type_separation
            else:
                required_separation = cross_type_separation

            if dist < required_separation:
                return False

        return True

    def _allowed_terrain_ids(
        self,
        sensor_type
    ):

        allowed = {
            PLAIN,
            FOREST,
            HILL,
            VALLEY,
            MOUNTAIN,
        }

        if getattr(self.cfg, "allow_water", False):
            allowed.add(
                WATER
            )

        return allowed

    # --------------------------------------------------
    # Separation lookup
    # --------------------------------------------------

    def _get_separation(
        self,
        sensor_type
    ):

        lookup = {
            "radar": self.cfg.radar_separation,
            "infrared": self.cfg.infrared_separation,
            "visual": self.cfg.visual_separation,
            "acoustic": self.cfg.acoustic_separation
        }

        return lookup.get(
            sensor_type,
            5
        )

    # --------------------------------------------------
    # Summary
    # --------------------------------------------------

    def summary(
        self,
        placed
    ):

        result = {}

        for sensor in placed:

            result.setdefault(
                sensor.sensor_type,
                0
            )

            result[
                sensor.sensor_type
            ] += 1

        return result