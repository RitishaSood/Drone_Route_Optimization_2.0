import heapq
import math
import time
from typing import Any, Dict, List, Optional, Tuple

import numpy as np


GridPoint = Tuple[int, int]  # row, col


class ThetaStarPlanner:
    """
    Threat-aware Theta* path planner over final_cost.csv.

    Internal coordinate convention:
    - row = matrix row
    - col = matrix column

    Frontend/API convention:
    - x = column
    - y = row
    """

    def __init__(
        self,
        cost_matrix: np.ndarray,
        threat_threshold: float = 999999.0,
    ):
        if cost_matrix.ndim != 2:
            raise ValueError("cost_matrix must be a 2D array")

        self.cost_matrix = cost_matrix.astype(float)
        self.rows, self.cols = self.cost_matrix.shape
        self.threat_threshold = float(threat_threshold)

        self.movements = [
            (0, 1, 1.0),
            (1, 0, 1.0),
            (0, -1, 1.0),
            (-1, 0, 1.0),
            (1, 1, math.sqrt(2)),
            (1, -1, math.sqrt(2)),
            (-1, 1, math.sqrt(2)),
            (-1, -1, math.sqrt(2)),
        ]

    def is_valid(self, row: int, col: int) -> bool:
        return 0 <= row < self.rows and 0 <= col < self.cols

    def is_blocked(self, row: int, col: int) -> bool:
        cell_cost = self.cost_matrix[row, col]
        return np.isinf(cell_cost) or cell_cost >= self.threat_threshold

    def is_traversable(self, row: int, col: int) -> bool:
        return self.is_valid(row, col) and not self.is_blocked(row, col)

    def heuristic(self, current: GridPoint, goal: GridPoint) -> float:
        dr = abs(current[0] - goal[0])
        dc = abs(current[1] - goal[1])

        diagonal = min(dr, dc)
        straight = max(dr, dc) - diagonal

        return math.sqrt(2) * diagonal + straight

    def line_of_sight_cost(self, start: GridPoint, end: GridPoint) -> Tuple[bool, float]:
        """
        Bresenham-style line-of-sight check.

        Returns:
        - has_los: whether all cells on the segment are traversable
        - los_cost: approximate cost of the smoothed segment
        """

        row0, col0 = start
        row1, col1 = end

        d_row = abs(row1 - row0)
        d_col = abs(col1 - col0)

        step_row = 1 if row0 < row1 else -1
        step_col = 1 if col0 < col1 else -1

        err = d_row - d_col

        row = row0
        col = col0

        total_cost = 0.0
        steps = 0

        while True:
            if not self.is_traversable(row, col):
                return False, float("inf")

            total_cost += float(self.cost_matrix[row, col])
            steps += 1

            if row == row1 and col == col1:
                break

            e2 = 2 * err

            if e2 > -d_col:
                err -= d_col
                row += step_row

            if e2 < d_row:
                err += d_row
                col += step_col

        segment_distance = math.sqrt((row1 - row0) ** 2 + (col1 - col0) ** 2)

        if steps > 0:
            average_cost = total_cost / steps
            return True, average_cost * segment_distance

        return False, float("inf")

    def plan(
        self,
        start: GridPoint,
        goal: GridPoint,
        fuel_capacity: Optional[float] = None,
    ) -> Dict[str, Any]:
        start_time = time.perf_counter()

        if not self.is_valid(*start):
            raise ValueError(f"Invalid start point: {start}")

        if not self.is_valid(*goal):
            raise ValueError(f"Invalid goal point: {goal}")

        if self.is_blocked(*start):
            return self._failed_result(
                start_time,
                "Start point is blocked or above threat threshold",
            )

        if self.is_blocked(*goal):
            return self._failed_result(
                start_time,
                "Goal point is blocked or above threat threshold",
            )

        open_heap = []
        heapq.heappush(open_heap, (self.heuristic(start, goal), start))

        parents: Dict[GridPoint, GridPoint] = {start: start}
        g_score: Dict[GridPoint, float] = {start: 0.0}

        closed_set = set()
        los_optimizations = 0
        nodes_visited = 0

        while open_heap:
            _, current = heapq.heappop(open_heap)

            if current in closed_set:
                continue

            closed_set.add(current)
            nodes_visited += 1

            if current == goal:
                runtime_seconds = time.perf_counter() - start_time
                path = self._reconstruct_path(parents, start, goal)

                return {
                    "success": True,
                    "path": path,
                    "total_cost": float(g_score[goal]),
                    "nodes_visited": nodes_visited,
                    "runtime_seconds": runtime_seconds,
                    "los_optimizations": los_optimizations,
                    "failure_reason": None,
                }

            current_parent = parents.get(current, current)

            for dr, dc, move_multiplier in self.movements:
                nr = current[0] + dr
                nc = current[1] + dc
                neighbor = (nr, nc)

                if not self.is_valid(nr, nc):
                    continue

                if self.is_blocked(nr, nc):
                    continue

                if neighbor in closed_set:
                    continue

                normal_step_cost = float(self.cost_matrix[nr, nc]) * move_multiplier
                normal_g = g_score[current] + normal_step_cost

                los_g = float("inf")
                tentative_parent = current

                has_los, los_cost = self.line_of_sight_cost(current_parent, neighbor)

                if has_los:
                    los_g = g_score[current_parent] + los_cost

                if los_g < normal_g:
                    tentative_g = los_g
                    tentative_parent = current_parent
                    used_los = True
                else:
                    tentative_g = normal_g
                    tentative_parent = current
                    used_los = False

                if fuel_capacity is not None and tentative_g > fuel_capacity:
                    continue

                if tentative_g < g_score.get(neighbor, float("inf")):
                    g_score[neighbor] = tentative_g
                    parents[neighbor] = tentative_parent

                    if used_los:
                        los_optimizations += 1

                    f_score = tentative_g + self.heuristic(neighbor, goal)
                    heapq.heappush(open_heap, (f_score, neighbor))

        return self._failed_result(
            start_time,
            "No feasible route within threshold/fuel constraints",
            nodes_visited=nodes_visited,
            los_optimizations=los_optimizations,
        )

    def _reconstruct_path(
        self,
        parents: Dict[GridPoint, GridPoint],
        start: GridPoint,
        goal: GridPoint,
    ) -> List[GridPoint]:
        path = []
        current = goal

        while current != start:
            path.append(current)
            current = parents[current]

        path.append(start)
        path.reverse()

        return path

    def _failed_result(
        self,
        start_time: float,
        reason: str,
        nodes_visited: int = 0,
        los_optimizations: int = 0,
    ) -> Dict[str, Any]:
        return {
            "success": False,
            "path": [],
            "total_cost": 0.0,
            "nodes_visited": nodes_visited,
            "runtime_seconds": time.perf_counter() - start_time,
            "los_optimizations": los_optimizations,
            "failure_reason": reason,
        }


def run_theta_star(
    cost_matrix: np.ndarray,
    start_xy: Tuple[int, int],
    goal_xy: Tuple[int, int],
    flight_z: int,
    threat_threshold: float = 999999.0,
    fuel_capacity: Optional[float] = None,
) -> Dict[str, Any]:
    """
    Pipeline-friendly Theta* entry point.

    Input convention:
    - start_xy = (x, y)
    - goal_xy = (x, y)

    Internal NumPy convention:
    - row = y
    - col = x
    """

    start_row_col = (start_xy[1], start_xy[0])
    goal_row_col = (goal_xy[1], goal_xy[0])

    planner = ThetaStarPlanner(
        cost_matrix=cost_matrix,
        threat_threshold=threat_threshold,
    )

    raw = planner.plan(
        start=start_row_col,
        goal=goal_row_col,
        fuel_capacity=fuel_capacity,
    )

    path_xy = [
        {
            "x": col,
            "y": row,
            "z": flight_z,
        }
        for row, col in raw["path"]
    ]

    return {
        "algorithm": "theta-star",
        "displayName": "Theta*",
        "status": "completed" if raw["success"] else "failed",
        "success": raw["success"],
        "runtimeMs": raw["runtime_seconds"] * 1000.0,
        "totalCost": raw["total_cost"],
        "nodesTraversed": len(path_xy),
        "nodesVisited": raw["nodes_visited"],
        "pathNodeCount": len(path_xy),
        "path": path_xy,
        "losOptimizations": raw.get("los_optimizations", 0),
        "failureReason": raw["failure_reason"],
        "pathCsv": "theta_star_path.csv",
        "pathPlot": "theta_star_path.png",
    }