import heapq
import math
import time
from typing import Any, Dict, List, Optional, Tuple

import numpy as np


GridPoint = Tuple[int, int]  # row, col


class AStarPlanner:
    """
    Threat-aware A* path planner over final_cost.csv.

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
        heuristic_type: str = "euclidean",
        threat_threshold: float = 999999.0,
    ):
        if cost_matrix.ndim != 2:
            raise ValueError("cost_matrix must be a 2D array")

        self.cost_matrix = cost_matrix.astype(float)
        self.rows, self.cols = self.cost_matrix.shape
        self.heuristic_type = heuristic_type.lower()
        self.threat_threshold = float(threat_threshold)

        self.movements = [
            (-1, 0, 1.0),
            (1, 0, 1.0),
            (0, -1, 1.0),
            (0, 1, 1.0),
            (-1, -1, math.sqrt(2)),
            (-1, 1, math.sqrt(2)),
            (1, -1, math.sqrt(2)),
            (1, 1, math.sqrt(2)),
        ]

        finite_costs = self.cost_matrix[np.isfinite(self.cost_matrix)]
        positive_costs = finite_costs[finite_costs > 0]

        if positive_costs.size > 0:
            self.min_step_cost = float(np.min(positive_costs))
        else:
            self.min_step_cost = 1.0

    def is_valid(self, row: int, col: int) -> bool:
        return 0 <= row < self.rows and 0 <= col < self.cols

    def is_blocked(self, row: int, col: int) -> bool:
        cell_cost = self.cost_matrix[row, col]
        return np.isinf(cell_cost) or cell_cost >= self.threat_threshold

    def heuristic(self, current: GridPoint, goal: GridPoint) -> float:
        row1, col1 = current
        row2, col2 = goal

        dr = abs(row1 - row2)
        dc = abs(col1 - col2)

        if self.heuristic_type == "manhattan":
            return (dr + dc) * self.min_step_cost

        if self.heuristic_type == "euclidean":
            return math.sqrt(dr * dr + dc * dc) * self.min_step_cost

        if self.heuristic_type == "octile":
            diagonal = min(dr, dc)
            straight = max(dr, dc) - diagonal
            return (math.sqrt(2) * diagonal + straight) * self.min_step_cost

        raise ValueError(f"Unknown heuristic type: {self.heuristic_type}")

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

        g_score: Dict[GridPoint, float] = {start: 0.0}
        came_from: Dict[GridPoint, GridPoint] = {}
        closed_set = set()

        start_h = self.heuristic(start, goal)
        heapq.heappush(open_heap, (start_h, 0.0, start))

        nodes_visited = 0

        while open_heap:
            _, current_g, current = heapq.heappop(open_heap)

            if current in closed_set:
                continue

            closed_set.add(current)
            nodes_visited += 1

            if current == goal:
                runtime_seconds = time.perf_counter() - start_time
                path = self._reconstruct_path(came_from, current, start)
                total_cost = self._path_total_cost(path)

                return {
                    "success": True,
                    "path": path,
                    "total_cost": total_cost,
                    "nodes_visited": nodes_visited,
                    "runtime_seconds": runtime_seconds,
                    "failure_reason": None,
                }

            row, col = current

            for dr, dc, move_multiplier in self.movements:
                nr = row + dr
                nc = col + dc
                neighbor = (nr, nc)

                if not self.is_valid(nr, nc):
                    continue

                if self.is_blocked(nr, nc):
                    continue

                if neighbor in closed_set:
                    continue

                step_cost = float(self.cost_matrix[nr, nc]) * move_multiplier
                tentative_g = current_g + step_cost

                if fuel_capacity is not None and tentative_g > fuel_capacity:
                    continue

                if tentative_g < g_score.get(neighbor, float("inf")):
                    came_from[neighbor] = current
                    g_score[neighbor] = tentative_g

                    f_score = tentative_g + self.heuristic(neighbor, goal)
                    heapq.heappush(open_heap, (f_score, tentative_g, neighbor))

        return self._failed_result(
            start_time,
            "No feasible path found",
            nodes_visited=nodes_visited,
        )

    def _path_total_cost(self, path: List[GridPoint]) -> float:
        return float(sum(float(self.cost_matrix[row, col]) for row, col in path))

    def _reconstruct_path(
        self,
        came_from: Dict[GridPoint, GridPoint],
        current: GridPoint,
        start: GridPoint,
    ) -> List[GridPoint]:
        path = [current]

        while current != start:
            current = came_from[current]
            path.append(current)

        path.reverse()
        return path

    def _failed_result(
        self,
        start_time: float,
        reason: str,
        nodes_visited: int = 0,
    ) -> Dict[str, Any]:
        return {
            "success": False,
            "path": [],
            "total_cost": 0.0,
            "nodes_visited": nodes_visited,
            "runtime_seconds": time.perf_counter() - start_time,
            "failure_reason": reason,
        }


def run_astar(
    cost_matrix: np.ndarray,
    start_xy: Tuple[int, int],
    goal_xy: Tuple[int, int],
    flight_z: int,
    heuristic_type: str = "octile",
    threat_threshold: float = 999999.0,
    fuel_capacity: Optional[float] = None,
    transition_cost_adapter: Any | None = None,
) -> Dict[str, Any]:
    """
    Pipeline-friendly A* entry point.

    Input convention:
    - start_xy = (x, y)
    - goal_xy = (x, y)

    Internal NumPy convention:
    - row = y
    - col = x
    """

    start_row_col = (start_xy[1], start_xy[0])
    goal_row_col = (goal_xy[1], goal_xy[0])

    planner = AStarPlanner(
        cost_matrix=cost_matrix,
        heuristic_type=heuristic_type,
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
        "algorithm": "astar",
        "displayName": "A*",
        "status": "completed" if raw["success"] else "failed",
        "success": raw["success"],
        "runtimeMs": raw["runtime_seconds"] * 1000.0,
        "totalCost": raw["total_cost"],
        "nodesTraversed": len(path_xy),
        "nodesVisited": raw["nodes_visited"],
        "pathNodeCount": len(path_xy),
        "path": path_xy,
        "failureReason": raw["failure_reason"],
        "pathCsv": "astar_path.csv",
        "pathPlot": "astar_path.png",
        "transitionAware": transition_cost_adapter is not None,
    }
