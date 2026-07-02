import math
import random
import time
from typing import Any, Dict, List, Optional, Tuple

import numpy as np


GridPointXY = Tuple[int, int]  # x, y


class BattlefieldGrid:
    """
    2D grid wrapper for ACO over final_cost.csv.

    ACO internal convention:
    - x = column
    - y = row

    NumPy convention:
    - matrix[y, x]
    """

    def __init__(self, cost_matrix: np.ndarray, threat_threshold: float = 999999.0):
        if cost_matrix.ndim != 2:
            raise ValueError("cost_matrix must be a 2D array")

        self.matrix = cost_matrix.astype(float)
        self.height, self.width = self.matrix.shape
        self.threat_threshold = float(threat_threshold)

        self.directions = [
            (0, -1, 1.0),
            (0, 1, 1.0),
            (-1, 0, 1.0),
            (1, 0, 1.0),
            (-1, -1, math.sqrt(2)),
            (-1, 1, math.sqrt(2)),
            (1, -1, math.sqrt(2)),
            (1, 1, math.sqrt(2)),
        ]

    def is_valid_coordinate(self, x: int, y: int) -> bool:
        return 0 <= x < self.width and 0 <= y < self.height

    def is_blocked(self, x: int, y: int) -> bool:
        cell_cost = self.matrix[y, x]
        return np.isinf(cell_cost) or cell_cost >= self.threat_threshold

    def get_neighbors(self, x: int, y: int) -> List[Tuple[int, int, float]]:
        neighbors = []

        for dx, dy, distance in self.directions:
            nx = x + dx
            ny = y + dy

            if not self.is_valid_coordinate(nx, ny):
                continue

            if self.is_blocked(nx, ny):
                continue

            neighbors.append((nx, ny, distance))

        return neighbors

    def calculate_step_cost(self, x: int, y: int, distance: float) -> float:
        return float(distance * self.matrix[y, x])


class AntColonyRoutePlanner:
    """
    Threat-aware Ant Colony Optimization planner.

    This is the heaviest algorithm in the current path-planner set because it uses:
    num_ants × iterations × path construction loops.
    """

    def __init__(
        self,
        grid: BattlefieldGrid,
        start: GridPointXY,
        goal: GridPointXY,
        num_ants: int = 30,
        iterations: int = 50,
        alpha: float = 1.0,
        beta: float = 2.0,
        rho: float = 0.1,
        q: float = 100.0,
        fuel_capacity: Optional[float] = None,
        max_path_length: int = 400,
        random_seed: Optional[int] = None,
    ):
        self.grid = grid
        self.start = start
        self.goal = goal

        self.num_ants = int(num_ants)
        self.iterations = int(iterations)

        self.alpha = float(alpha)
        self.beta = float(beta)
        self.rho = float(rho)
        self.q = float(q)

        self.fuel_capacity = fuel_capacity
        self.max_path_length = int(max_path_length)

        self.pheromones = np.full((grid.height, grid.width), 1.0, dtype=float)

        self.best_path: Optional[List[GridPointXY]] = None
        self.best_cost = float("inf")
        self.convergence_history: List[Optional[float]] = []

        self.nodes_visited = 0
        self.successful_ants = 0
        self.failed_ants = 0

        if random_seed is not None:
            random.seed(random_seed)
            np.random.seed(random_seed)

    def _distance_to_goal(self, x: int, y: int) -> float:
        gx, gy = self.goal
        return math.sqrt((gx - x) ** 2 + (gy - y) ** 2)

    def _get_heuristic(self, x: int, y: int, distance: float) -> float:
        """
        ACO desirability.

        Combines:
        - low movement/cost cells
        - closeness to goal

        This makes ACO less likely to wander randomly.
        """

        step_cost = self.grid.calculate_step_cost(x, y, distance)
        goal_distance = self._distance_to_goal(x, y)

        return 1.0 / ((step_cost + 1e-6) * (goal_distance + 1.0))

    def _construct_ant_path(self) -> Tuple[List[GridPointXY], float, bool]:
        path = [self.start]
        visited = {self.start}

        total_cost = 0.0

        while path[-1] != self.goal:
            current_x, current_y = path[-1]

            neighbors = self.grid.get_neighbors(current_x, current_y)
            unvisited = [
                (nx, ny, distance)
                for nx, ny, distance in neighbors
                if (nx, ny) not in visited
            ]

            if not unvisited:
                return path, total_cost, False

            probabilities = []
            candidates = []

            for nx, ny, distance in unvisited:
                step_cost = self.grid.calculate_step_cost(nx, ny, distance)

                if self.fuel_capacity is not None and total_cost + step_cost > self.fuel_capacity:
                    continue

                tau = self.pheromones[ny, nx] ** self.alpha
                eta = self._get_heuristic(nx, ny, distance) ** self.beta

                probability_weight = tau * eta

                probabilities.append(probability_weight)
                candidates.append((nx, ny, step_cost))

            if not candidates:
                return path, total_cost, False

            probability_sum = sum(probabilities)

            if probability_sum <= 0:
                probabilities = [1.0 / len(candidates)] * len(candidates)
            else:
                probabilities = [p / probability_sum for p in probabilities]

            selected_index = random.choices(
                range(len(candidates)),
                weights=probabilities,
                k=1,
            )[0]

            next_x, next_y, step_cost = candidates[selected_index]

            path.append((next_x, next_y))
            visited.add((next_x, next_y))

            total_cost += step_cost
            self.nodes_visited += 1

            if len(path) > self.max_path_length:
                return path, total_cost, False

        return path, total_cost, True

    def optimize(self) -> Dict[str, Any]:
        start_time = time.perf_counter()

        if not self.grid.is_valid_coordinate(*self.start):
            return self._failed_result(start_time, "Invalid start point")

        if not self.grid.is_valid_coordinate(*self.goal):
            return self._failed_result(start_time, "Invalid goal point")

        if self.grid.is_blocked(*self.start):
            return self._failed_result(
                start_time,
                "Start point is blocked or above threat threshold",
            )

        if self.grid.is_blocked(*self.goal):
            return self._failed_result(
                start_time,
                "Goal point is blocked or above threat threshold",
            )

        for _ in range(self.iterations):
            iteration_paths = []
            iteration_costs = []

            for _ in range(self.num_ants):
                path, cost, success = self._construct_ant_path()

                if success:
                    self.successful_ants += 1
                    iteration_paths.append(path)
                    iteration_costs.append(cost)
                else:
                    self.failed_ants += 1

            self.pheromones *= 1.0 - self.rho

            for path, cost in zip(iteration_paths, iteration_costs):
                if cost <= 0:
                    continue

                deposit = self.q / cost

                for x, y in path:
                    self.pheromones[y, x] += deposit

            if iteration_costs:
                best_iteration_cost = min(iteration_costs)
                best_index = iteration_costs.index(best_iteration_cost)

                if best_iteration_cost < self.best_cost:
                    self.best_cost = best_iteration_cost
                    self.best_path = iteration_paths[best_index]

            self.convergence_history.append(
                self.best_cost if self.best_cost != float("inf") else None
            )

        runtime_seconds = time.perf_counter() - start_time

        if self.best_path is None:
            return {
                "success": False,
                "path": [],
                "total_cost": 0.0,
                "nodes_visited": self.nodes_visited,
                "runtime_seconds": runtime_seconds,
                "convergence_history": self.convergence_history,
                "successful_ants": self.successful_ants,
                "failed_ants": self.failed_ants,
                "failure_reason": "No feasible path found by ACO",
            }

        return {
            "success": True,
            "path": self.best_path,
            "total_cost": float(self.best_cost),
            "nodes_visited": self.nodes_visited,
            "runtime_seconds": runtime_seconds,
            "convergence_history": self.convergence_history,
            "successful_ants": self.successful_ants,
            "failed_ants": self.failed_ants,
            "failure_reason": None,
        }

    def _failed_result(self, start_time: float, reason: str) -> Dict[str, Any]:
        return {
            "success": False,
            "path": [],
            "total_cost": 0.0,
            "nodes_visited": 0,
            "runtime_seconds": time.perf_counter() - start_time,
            "convergence_history": [],
            "successful_ants": 0,
            "failed_ants": 0,
            "failure_reason": reason,
        }


def run_ant_colony(
    cost_matrix: np.ndarray,
    start_xy: Tuple[int, int],
    goal_xy: Tuple[int, int],
    flight_z: int,
    threat_threshold: float = 999999.0,
    fuel_capacity: Optional[float] = None,
    num_ants: int = 30,
    iterations: int = 50,
    alpha: float = 1.0,
    beta: float = 2.0,
    rho: float = 0.1,
    q: float = 100.0,
    max_path_length: int = 400,
    random_seed: Optional[int] = 42,
) -> Dict[str, Any]:
    """
    Pipeline-friendly ACO entry point.

    Input convention:
    - start_xy = (x, y)
    - goal_xy = (x, y)

    Internal ACO convention:
    - x = column
    - y = row
    """

    grid = BattlefieldGrid(
        cost_matrix=cost_matrix,
        threat_threshold=threat_threshold,
    )

    planner = AntColonyRoutePlanner(
        grid=grid,
        start=start_xy,
        goal=goal_xy,
        num_ants=num_ants,
        iterations=iterations,
        alpha=alpha,
        beta=beta,
        rho=rho,
        q=q,
        fuel_capacity=fuel_capacity,
        max_path_length=max_path_length,
        random_seed=random_seed,
    )

    raw = planner.optimize()

    path_xy = [
        {
            "x": x,
            "y": y,
            "z": flight_z,
        }
        for x, y in raw["path"]
    ]

    return {
        "algorithm": "ant-colony",
        "displayName": "Ant Colony Optimization",
        "status": "completed" if raw["success"] else "failed",
        "success": raw["success"],
        "runtimeMs": raw["runtime_seconds"] * 1000.0,
        "totalCost": raw["total_cost"],
        "nodesTraversed": len(path_xy),
        "nodesVisited": raw["nodes_visited"],
        "pathNodeCount": len(path_xy),
        "path": path_xy,
        "successfulAnts": raw.get("successful_ants", 0),
        "failedAnts": raw.get("failed_ants", 0),
        "convergenceHistory": raw.get("convergence_history", []),
        "failureReason": raw["failure_reason"],
        "pathCsv": "ant_colony_path.csv",
        "pathPlot": "ant_colony_path.png",
    }