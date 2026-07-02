import heapq
import math
import time
from typing import Any, Dict, List, Optional, Tuple

import numpy as np


GridPoint = Tuple[int, int]  # row, col


class BattlefieldGrid:
    """
    2D grid wrapper for route planning over final_cost.csv.

    Internal coordinate convention:
    - row = matrix row
    - col = matrix column

    Frontend/API convention should be:
    - x = column
    - y = row
    """

    def __init__(self, cost_matrix: np.ndarray, threat_threshold: float):
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
            (-1, 1, math.sqrt(2)),
            (1, -1, math.sqrt(2)),
            (-1, -1, math.sqrt(2)),
        ]

    def is_valid(self, row: int, col: int) -> bool:
        return 0 <= row < self.rows and 0 <= col < self.cols

    def is_blocked(self, row: int, col: int) -> bool:
        cell_cost = self.cost_matrix[row, col]
        return np.isinf(cell_cost) or cell_cost >= self.threat_threshold

    def get_neighbors(self, row: int, col: int) -> List[Tuple[int, int, float]]:
        neighbors = []

        for dr, dc, move_multiplier in self.movements:
            nr = row + dr
            nc = col + dc

            if not self.is_valid(nr, nc):
                continue

            if self.is_blocked(nr, nc):
                continue

            cell_cost = self.cost_matrix[nr, nc]
            transition_cost = move_multiplier * float(cell_cost)

            neighbors.append((nr, nc, transition_cost))

        return neighbors


class DijkstraPlanner:
    """Threat-aware Dijkstra path planner."""

    def __init__(self, grid: BattlefieldGrid):
        self.grid = grid

    def plan(
        self,
        start: GridPoint,
        goal: GridPoint,
        fuel_capacity: Optional[float] = None,
    ) -> Dict[str, Any]:
        start_time = time.perf_counter()

        if not self.grid.is_valid(*start):
            raise ValueError(f"Invalid start point: {start}")

        if not self.grid.is_valid(*goal):
            raise ValueError(f"Invalid goal point: {goal}")

        if self.grid.is_blocked(*start):
            return self._failed_result(
                start_time=start_time,
                reason="Start point is blocked or above threat threshold",
            )

        if self.grid.is_blocked(*goal):
            return self._failed_result(
                start_time=start_time,
                reason="Goal point is blocked or above threat threshold",
            )

        priority_queue = [(0.0, start[0], start[1])]

        distances = np.full((self.grid.rows, self.grid.cols), np.inf)
        distances[start[0], start[1]] = 0.0

        parent_map: Dict[GridPoint, GridPoint] = {}
        visited = set()

        nodes_visited = 0
        success = False

        while priority_queue:
            current_cost, row, col = heapq.heappop(priority_queue)

            if current_cost > distances[row, col]:
                continue

            if (row, col) in visited:
                continue

            visited.add((row, col))
            nodes_visited += 1

            if (row, col) == goal:
                success = True
                break

            for nr, nc, transition_cost in self.grid.get_neighbors(row, col):
                next_cost = current_cost + transition_cost

                if fuel_capacity is not None and next_cost > fuel_capacity:
                    continue

                if next_cost < distances[nr, nc]:
                    distances[nr, nc] = next_cost
                    parent_map[(nr, nc)] = (row, col)
                    heapq.heappush(priority_queue, (next_cost, nr, nc))

        runtime_seconds = time.perf_counter() - start_time

        if not success:
            return {
                "success": False,
                "path": [],
                "total_cost": 0.0,
                "nodes_visited": nodes_visited,
                "runtime_seconds": runtime_seconds,
                "failure_reason": "No feasible path found",
            }

        path = self._reconstruct_path(start, goal, parent_map)
        total_cost = float(distances[goal[0], goal[1]])

        return {
            "success": True,
            "path": path,
            "total_cost": total_cost,
            "nodes_visited": nodes_visited,
            "runtime_seconds": runtime_seconds,
            "failure_reason": None,
        }

    def _reconstruct_path(
        self,
        start: GridPoint,
        goal: GridPoint,
        parent_map: Dict[GridPoint, GridPoint],
    ) -> List[GridPoint]:
        path = []
        current = goal

        while current != start:
            path.append(current)
            current = parent_map[current]

        path.append(start)
        path.reverse()

        return path

    def _failed_result(self, start_time: float, reason: str) -> Dict[str, Any]:
        return {
            "success": False,
            "path": [],
            "total_cost": 0.0,
            "nodes_visited": 0,
            "runtime_seconds": time.perf_counter() - start_time,
            "failure_reason": reason,
        }


def run_dijkstra(
    cost_matrix: np.ndarray,
    start_xy: Tuple[int, int],
    goal_xy: Tuple[int, int],
    flight_z: int,
    threat_threshold: float = 999999.0,
    fuel_capacity: Optional[float] = None,
) -> Dict[str, Any]:
    """
    Pipeline-friendly Dijkstra entry point.

    Input convention:
    - start_xy = (x, y)
    - goal_xy = (x, y)

    Internal convention:
    - row = y
    - col = x
    """

    start_row_col = (start_xy[1], start_xy[0])
    goal_row_col = (goal_xy[1], goal_xy[0])

    grid = BattlefieldGrid(cost_matrix, threat_threshold=threat_threshold)
    planner = DijkstraPlanner(grid)

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
        "algorithm": "dijkstra",
        "displayName": "Dijkstra",
        "status": "completed" if raw["success"] else "failed",
        "success": raw["success"],
        "runtimeMs": raw["runtime_seconds"] * 1000.0,
        "totalCost": raw["total_cost"],
        "nodesTraversed": len(path_xy),
        "nodesVisited": raw["nodes_visited"],
        "pathNodeCount": len(path_xy),
        "path": path_xy,
        "failureReason": raw["failure_reason"],
        "pathCsv": "dijkstra_path.csv",
        "pathPlot": "dijkstra_path.png",
    }