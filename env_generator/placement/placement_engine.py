from __future__ import annotations

import numpy as np

from placement.sensor_types import SENSOR_TYPES
from placement.placed_sensor import PlacedSensor
from placement.nfz import NFZLoader

from terrain.terrain_constants import WATER


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

        sensor_id = starting_id

        # Divide map into zones for distributed placement.
        # 4 x 4 = 16 zones for a 100 x 100 map.
        zone_count_x = 4
        zone_count_y = 4

        zone_size_x = self.height_map.shape[0] // zone_count_x
        zone_size_y = self.height_map.shape[1] // zone_count_y

        zones = []

        for zx in range(
            zone_count_x
        ):
            for zy in range(
                zone_count_y
            ):

                x_start = zx * zone_size_x

                x_end = (
                    self.height_map.shape[0]
                    if zx == zone_count_x - 1
                    else (zx + 1) * zone_size_x
                )

                y_start = zy * zone_size_y

                y_end = (
                    self.height_map.shape[1]
                    if zy == zone_count_y - 1
                    else (zy + 1) * zone_size_y
                )

                zone_score = float(
                    np.mean(
                        suitability[
                            x_start:x_end,
                            y_start:y_end
                        ]
                    )
                )

                zones.append(
                    (
                        zone_score,
                        x_start,
                        x_end,
                        y_start,
                        y_end
                    )
                )

        zones.sort(
            key=lambda z: z[0],
            reverse=True
        )

        # Try to place one sensor per zone per round.
        # This avoids placing all sensors in the single best region.
        while len(placed) < count:

            placed_this_round = False

            for _, x_start, x_end, y_start, y_end in zones:

                if len(placed) >= count:
                    break

                zone_suitability = suitability[
                    x_start:x_end,
                    y_start:y_end
                ]

                flat_indices = np.argsort(
                    zone_suitability.ravel()
                )[::-1]

                candidates = np.column_stack(
                    np.unravel_index(
                        flat_indices,
                        zone_suitability.shape
                    )
                )

                for local_x, local_y in candidates:

                    x = int(
                        x_start + local_x
                    )

                    y = int(
                        y_start + local_y
                    )

                    if not self._valid_location(
                        x,
                        y,
                        sensor_type,
                        existing_sensors + placed
                    ):
                        continue

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

                    placed_this_round = True

                    break

            if not placed_this_round:
                break

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

        # Water forbidden
        if self.terrain_map[x, y] == WATER:
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