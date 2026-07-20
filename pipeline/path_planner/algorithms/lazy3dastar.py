from __future__ import annotations

import heapq
import math
import time
from typing import Any, Dict, List, Optional, Tuple

import numpy as np


GridPoint3D = Tuple[int, int, int]


class Lazy3DAStarPlanner:
    def __init__(
        self,
        cost_matrix: np.ndarray,
        threat_threshold: float = 999999.0,
        terrain_height: Optional[np.ndarray] = None,
        z_min: int = 0,
        z_max: int = 99,
        preferred_z: int = 50,
        altitude_penalty_weight: float = 1.0,
    ):
        if cost_matrix.ndim != 2:
            raise ValueError("cost_matrix must be a 2D array")
        self.cost_matrix = cost_matrix.astype(float)
        self.rows, self.cols = self.cost_matrix.shape
        self.threat_threshold = float(threat_threshold)
        self.terrain_height = terrain_height.astype(float) if terrain_height is not None else None
        self.z_min = int(z_min)
        self.z_max = int(z_max)
        self.preferred_z = int(preferred_z)
        self.altitude_penalty_weight = float(altitude_penalty_weight)

    def is_valid(self, x: int, y: int) -> bool:
        return 0 <= x < self.cols and 0 <= y < self.rows

    def is_blocked(self, x: int, y: int) -> bool:
        cell_cost = self.cost_matrix[y, x]
        return np.isinf(cell_cost) or cell_cost >= self.threat_threshold

    def is_valid_state(self, x: int, y: int, z: int) -> bool:
        if not self.is_valid(x, y):
            return False
        if z < self.z_min or z > self.z_max:
            return False
        if self.terrain_height is not None and z <= float(self.terrain_height[y, x]):
            return False
        return not self.is_blocked(x, y)

    def heuristic(self, a: GridPoint3D, b: GridPoint3D) -> float:
        dx = abs(a[0] - b[0])
        dy = abs(a[1] - b[1])
        dz = abs(a[2] - b[2])
        return math.sqrt(dx * dx + dy * dy + (dz * 0.1) * (dz * 0.1))

    def plan(
        self,
        start: GridPoint3D,
        goal: GridPoint3D,
        fuel_capacity: Optional[float] = None,
    ) -> Dict[str, Any]:
        start_time = time.perf_counter()

        if not self.is_valid(start[0], start[1]):
            raise ValueError(f"Invalid start point: {start}")
        if not self.is_valid(goal[0], goal[1]):
            raise ValueError(f"Invalid goal point: {goal}")
        if self.is_blocked(start[0], start[1]):
            return self._failed_result(start_time, "Start point is blocked or above threat threshold")
        if self.is_blocked(goal[0], goal[1]):
            return self._failed_result(start_time, "Goal point is blocked or above threat threshold")

        start_state = (start[0], start[1], start[2])
        goal_state = (goal[0], goal[1], goal[2])

        open_heap: list[tuple[float, float, GridPoint3D]] = []
        came_from: dict[GridPoint3D, GridPoint3D] = {}
        g_score: dict[GridPoint3D, float] = {start_state: 0.0}
        closed: set[GridPoint3D] = set()

        heapq.heappush(open_heap, (self.heuristic(start_state, goal_state), 0.0, start_state))
        nodes_visited = 0

        while open_heap:
            _, current_g, current = heapq.heappop(open_heap)
            if current in closed:
                continue
            closed.add(current)
            nodes_visited += 1

            if current == goal_state:
                path = self._reconstruct_path(came_from, current, start_state)
                return {
                    "success": True,
                    "path": path,
                    "total_cost": self._path_total_cost(path),
                    "nodes_visited": nodes_visited,
                    "runtime_seconds": time.perf_counter() - start_time,
                    "failure_reason": None,
                }

            x, y, z = current
            for nx, ny, nz, step_cost in self._neighbors(x, y, z):
                if not self.is_valid_state(nx, ny, nz):
                    continue
                neighbor = (nx, ny, nz)
                if neighbor in closed:
                    continue
                tentative = current_g + step_cost
                if fuel_capacity is not None and tentative > fuel_capacity:
                    continue
                if tentative < g_score.get(neighbor, float("inf")):
                    came_from[neighbor] = current
                    g_score[neighbor] = tentative
                    heapq.heappush(open_heap, (tentative + self.heuristic(neighbor, goal_state), tentative, neighbor))

        return self._failed_result(start_time, "No feasible path found", nodes_visited=nodes_visited)

    def _neighbors(self, x: int, y: int, z: int) -> list[tuple[int, int, int, float]]:
        neighbors: list[tuple[int, int, int, float]] = []
        for dx in (-1, 0, 1):
            for dy in (-1, 0, 1):
                for dz in (-1, 0, 1):
                    if dx == dy == dz == 0:
                        continue
                    nx = x + dx
                    ny = y + dy
                    nz = z + dz
                    if not self.is_valid(nx, ny):
                        continue
                    if dz == 0:
                        cost = float(self.cost_matrix[ny, nx])
                    else:
                        cost = float(self.cost_matrix[ny, nx]) + abs(nz - self.preferred_z) * self.altitude_penalty_weight
                    if not math.isfinite(cost):
                        continue
                    step = math.sqrt(dx * dx + dy * dy + (dz * 0.1) * (dz * 0.1))
                    neighbors.append((nx, ny, nz, cost * step))
        return neighbors

    def _reconstruct_path(self, came_from: dict[GridPoint3D, GridPoint3D], current: GridPoint3D, start: GridPoint3D) -> List[GridPoint3D]:
        path = [current]
        while current != start:
            current = came_from[current]
            path.append(current)
        path.reverse()
        return path

    def _path_total_cost(self, path: List[GridPoint3D]) -> float:
        if len(path) < 2:
            return 0.0

        total = 0.0
        for prev, curr in zip(path, path[1:]):
            dx = curr[0] - prev[0]
            dy = curr[1] - prev[1]
            dz = curr[2] - prev[2]
            step_length = math.sqrt(dx * dx + dy * dy + (dz * 0.1) * (dz * 0.1))
            cell_cost = float(self.cost_matrix[curr[1], curr[0]])
            altitude_penalty = abs(curr[2] - self.preferred_z) * self.altitude_penalty_weight
            total += (cell_cost + altitude_penalty) * step_length
        return float(total)

    def _failed_result(self, start_time: float, reason: str, nodes_visited: int = 0) -> Dict[str, Any]:
        return {
            "success": False,
            "path": [],
            "total_cost": 0.0,
            "nodes_visited": nodes_visited,
            "runtime_seconds": time.perf_counter() - start_time,
            "failure_reason": reason,
        }


def run_lazy_3d_astar(
    cost_matrix: np.ndarray,
    start_xyz: Tuple[int, int, int],
    goal_xyz: Tuple[int, int, int],
    terrain_height: Optional[np.ndarray] = None,
    z_min: int = 0,
    z_max: int = 99,
    preferred_z: Optional[int] = None,
    altitude_penalty_weight: float = 1.0,
    threat_threshold: float = 999999.0,
    fuel_capacity: Optional[float] = None,
) -> Dict[str, Any]:
    preferred_z = start_xyz[2] if preferred_z is None else preferred_z
    planner = Lazy3DAStarPlanner(
        cost_matrix,
        threat_threshold=threat_threshold,
        terrain_height=terrain_height,
        z_min=z_min,
        z_max=z_max,
        preferred_z=preferred_z,
        altitude_penalty_weight=altitude_penalty_weight,
    )
    raw = planner.plan(start_xyz, goal_xyz, fuel_capacity=fuel_capacity)
    path_xyz = [{"x": x, "y": y, "z": z} for x, y, z in raw["path"]]
    return {
        "algorithm": "lazy-3d-astar",
        "displayName": "Lazy 3D A*",
        "status": "completed" if raw["success"] else "failed",
        "success": raw["success"],
        "gridMode": "Mode3D",
        "planningMode": "3D",
        "transitionAware": True,
        "runtimeMs": raw["runtime_seconds"] * 1000.0,
        "totalCost": float(raw["total_cost"]),
        "nodesTraversed": len(path_xyz),
        "nodesVisited": raw["nodes_visited"],
        "pathNodeCount": len(path_xyz),
        "path": path_xyz,
        "failureReason": raw["failure_reason"],
        "pathCsv": "lazy_3d_astar_path.csv",
        "pathJson": "lazy_3d_astar_path.json",
        "pathPlot": "lazy_3d_route.png",
        "routePlot": "lazy_3d_route_over_terrain.png",
        "altitudePlot": "lazy_3d_altitude_profile.png",
        "costPlot": "lazy_3d_cost_profile.png",
        "statsPlot": "lazy_3d_stats_summary.png",
        "startX": start_xyz[0],
        "startY": start_xyz[1],
        "startZ": start_xyz[2],
        "goalX": goal_xyz[0],
        "goalY": goal_xyz[1],
        "goalZ": goal_xyz[2],
        "zMin": z_min,
        "zMax": z_max,
        "preferredZ": preferred_z,
        "altitudePenaltyWeight": altitude_penalty_weight,
    }
