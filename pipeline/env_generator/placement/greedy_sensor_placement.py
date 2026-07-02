import math
import random


class GreedySensorPlacement:
    def __init__(self, grid_size=100, min_distance=12, seed=42):
        self.grid_size = grid_size
        self.min_distance = min_distance
        random.seed(seed)

    def coord_to_index(self, x, y):
        """
        Converts bottom-left origin coordinates to top-left matrix indexing.

        Coordinate system:
        - (0, 0) is bottom-left
        - x increases right
        - y increases upward

        Matrix indexing:
        - row 0 is top
        - col 0 is left
        """
        row = self.grid_size - 1 - y
        col = x
        return row, col

    def distance(self, a, b):
        ax, ay = a
        bx, by = b
        return math.sqrt((ax - bx) ** 2 + (ay - by) ** 2)

    def is_far_enough(self, candidate, placed):
        for p in placed:
            if self.distance(candidate, p) < self.min_distance:
                return False
        return True

    def get_quadrants(self):
        mid = self.grid_size // 2

        return [
            {
                "name": "bottom_left",
                "bounds": (0, mid - 1, 0, mid - 1),
            },
            {
                "name": "bottom_right",
                "bounds": (mid, self.grid_size - 1, 0, mid - 1),
            },
            {
                "name": "top_left",
                "bounds": (0, mid - 1, mid, self.grid_size - 1),
            },
            {
                "name": "top_right",
                "bounds": (mid, self.grid_size - 1, mid, self.grid_size - 1),
            },
        ]

    def get_candidates(
        self,
        suitability_map,
        terrain_type_map,
        bounds=None,
        allowed_terrain_ids=None,
        is_valid_location=None,
    ):
        candidates = []

        if bounds is None:
            x_min = 0
            x_max = self.grid_size - 1
            y_min = 0
            y_max = self.grid_size - 1
        else:
            x_min, x_max, y_min, y_max = bounds

        for y in range(y_min, y_max + 1):
            for x in range(x_min, x_max + 1):
                row, col = self.coord_to_index(x, y)

                score = float(suitability_map[row][col])
                terrain_id = int(terrain_type_map[row][col])

                if allowed_terrain_ids is not None:
                    if terrain_id not in allowed_terrain_ids:
                        continue

                if score <= 0:
                    continue

                if is_valid_location is not None:
                    if not is_valid_location(x, y):
                        continue

                candidates.append((x, y, score))

        candidates.sort(key=lambda item: item[2], reverse=True)
        return candidates

    def greedy_pick_from_candidates(self, candidates, quota, placed):
        selected = []

        for x, y, score in candidates:
            candidate = (x, y)

            if self.is_far_enough(candidate, placed):
                selected.append(candidate)
                placed.append(candidate)

            if len(selected) >= quota:
                break

        return selected

    def place_sensors(
        self,
        suitability_map,
        terrain_type_map,
        total_sensors,
        allowed_terrain_ids=None,
        existing_coords=None,
        is_valid_location=None,
        debug_label=None,
    ):
        quadrants = self.get_quadrants()

        sensors_per_quadrant = total_sensors // 4
        remainder = total_sensors % 4

        placed = list(existing_coords or [])
        selected_coords = []
        quadrant_counts = {}
        leftovers = 0

        for q_index, quadrant in enumerate(quadrants):
            quota = sensors_per_quadrant

            if q_index < remainder:
                quota += 1

            candidates = self.get_candidates(
                suitability_map=suitability_map,
                terrain_type_map=terrain_type_map,
                bounds=quadrant["bounds"],
                allowed_terrain_ids=allowed_terrain_ids,
                is_valid_location=is_valid_location,
            )

            selected = self.greedy_pick_from_candidates(
                candidates=candidates,
                quota=quota,
                placed=placed,
            )

            selected_coords.extend(selected)
            quadrant_counts[quadrant["name"]] = len(selected)

            if len(selected) < quota:
                leftovers += quota - len(selected)

        if leftovers > 0:
            global_candidates = self.get_candidates(
                suitability_map=suitability_map,
                terrain_type_map=terrain_type_map,
                bounds=None,
                allowed_terrain_ids=allowed_terrain_ids,
                is_valid_location=is_valid_location,
            )

            extra_selected = self.greedy_pick_from_candidates(
                candidates=global_candidates,
                quota=leftovers,
                placed=placed,
            )

            selected_coords.extend(extra_selected)
            quadrant_counts["global_fallback"] = len(extra_selected)

        label = f" for {debug_label}" if debug_label else ""
        print(f"[PLACEMENT] Greedy quadrant placement summary{label}:")
        for name, count in quadrant_counts.items():
            print(f"  {name}: {count}")

        return selected_coords