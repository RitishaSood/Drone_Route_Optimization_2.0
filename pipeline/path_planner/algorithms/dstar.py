import heapq
import math
import time
from typing import Any, Dict, List, Optional, Tuple

import numpy as np


GridPoint = Tuple[int, int]  # row, col


class PriorityQueue:
    """Lazy-deletion priority queue for D* Lite."""

    def __init__(self):
        self.heap = []
        self.vertices = {}
        self.counter = 0

    def insert(self, vertex: GridPoint, key: Tuple[float, float]) -> None:
        if vertex in self.vertices:
            self.remove(vertex)

        entry = [key[0], key[1], self.counter, vertex]
        self.counter += 1
        self.vertices[vertex] = entry
        heapq.heappush(self.heap, entry)

    def remove(self, vertex: GridPoint) -> None:
        if vertex in self.vertices:
            entry = self.vertices.pop(vertex)
            entry[-1] = None

    def pop(self) -> Optional[Tuple[GridPoint, Tuple[float, float]]]:
        while self.heap:
            k0, k1, _, vertex = heapq.heappop(self.heap)

            if vertex is not None:
                self.vertices.pop(vertex, None)
                return vertex, (k0, k1)

        return None

    def top_key(self) -> Tuple[float, float]:
        while self.heap:
            k0, k1, _, vertex = self.heap[0]

            if vertex is not None:
                return (k0, k1)

            heapq.heappop(self.heap)

        return (float("inf"), float("inf"))

    def contains(self, vertex: GridPoint) -> bool:
        return vertex in self.vertices


class DStarLitePlanner:
    """
    D* Lite planner over final_cost.csv.

    Internal convention:
    - row = matrix row
    - col = matrix column

    Frontend/API convention:
    - x = column
    - y = row
    """

    def __init__(
        self,
        cost_matrix: np.ndarray,
        start: GridPoint,
        goal: GridPoint,
        threat_threshold: float = 999999.0,
    ):
        if cost_matrix.ndim != 2:
            raise ValueError("cost_matrix must be a 2D array")

        self.cost_matrix = cost_matrix.astype(float)
        self.rows, self.cols = self.cost_matrix.shape

        self.start = start
        self.current_position = start
        self.goal = goal
        self.threat_threshold = float(threat_threshold)

        self.g: Dict[GridPoint, float] = {}
        self.rhs: Dict[GridPoint, float] = {}

        self.km = 0.0
        self.u_queue = PriorityQueue()

        self.nodes_visited = 0

        self.movements = [
            (-1, 0),
            (1, 0),
            (0, -1),
            (0, 1),
            (-1, -1),
            (-1, 1),
            (1, -1),
            (1, 1),
        ]

        self._validate_start_goal()
        self.initialize()

    def _validate_start_goal(self) -> None:
        if not self.is_valid(*self.start):
            raise ValueError(f"Invalid start point: {self.start}")

        if not self.is_valid(*self.goal):
            raise ValueError(f"Invalid goal point: {self.goal}")

    def initialize(self) -> None:
        self.rhs[self.goal] = 0.0
        self.u_queue.insert(self.goal, self.calculate_key(self.goal))

    def is_valid(self, row: int, col: int) -> bool:
        return 0 <= row < self.rows and 0 <= col < self.cols

    def is_blocked(self, row: int, col: int) -> bool:
        cell_cost = self.cost_matrix[row, col]
        return np.isinf(cell_cost) or cell_cost >= self.threat_threshold

    def get_g(self, point: GridPoint) -> float:
        return self.g.get(point, float("inf"))

    def get_rhs(self, point: GridPoint) -> float:
        return self.rhs.get(point, float("inf"))

    def heuristic(self, a: GridPoint, b: GridPoint) -> float:
        dr = abs(a[0] - b[0])
        dc = abs(a[1] - b[1])

        diagonal = min(dr, dc)
        straight = max(dr, dc) - diagonal

        return math.sqrt(2) * diagonal + straight

    def calculate_key(self, point: GridPoint) -> Tuple[float, float]:
        g_rhs = min(self.get_g(point), self.get_rhs(point))
        return (
            g_rhs + self.heuristic(self.current_position, point) + self.km,
            g_rhs,
        )

    def get_neighbors(self, point: GridPoint) -> List[GridPoint]:
        row, col = point
        neighbors = []

        for dr, dc in self.movements:
            nr = row + dr
            nc = col + dc

            if not self.is_valid(nr, nc):
                continue

            if self.is_blocked(nr, nc):
                continue

            neighbors.append((nr, nc))

        return neighbors

    def transition_cost(self, a: GridPoint, b: GridPoint) -> float:
        diagonal = a[0] != b[0] and a[1] != b[1]
        step_distance = math.sqrt(2) if diagonal else 1.0

        avg_cell_cost = (
            float(self.cost_matrix[a[0], a[1]])
            + float(self.cost_matrix[b[0], b[1]])
        ) / 2.0

        return step_distance * avg_cell_cost

    def update_vertex(self, point: GridPoint) -> None:
        if point != self.goal:
            neighbors = self.get_neighbors(point)

            if neighbors:
                self.rhs[point] = min(
                    self.transition_cost(point, neighbor) + self.get_g(neighbor)
                    for neighbor in neighbors
                )
            else:
                self.rhs[point] = float("inf")

        if self.u_queue.contains(point):
            self.u_queue.remove(point)

        if self.get_g(point) != self.get_rhs(point):
            self.u_queue.insert(point, self.calculate_key(point))

    def compute_shortest_path(self) -> None:
        while (
            self.u_queue.top_key() < self.calculate_key(self.current_position)
            or self.get_rhs(self.current_position) != self.get_g(self.current_position)
        ):
            popped = self.u_queue.pop()

            if popped is None:
                break

            point, old_key = popped
            self.nodes_visited += 1

            new_key = self.calculate_key(point)

            if old_key < new_key:
                self.u_queue.insert(point, new_key)

            elif self.get_g(point) > self.get_rhs(point):
                self.g[point] = self.get_rhs(point)

                for neighbor in self.get_neighbors(point):
                    self.update_vertex(neighbor)

            else:
                self.g[point] = float("inf")
                self.update_vertex(point)

                for neighbor in self.get_neighbors(point):
                    self.update_vertex(neighbor)

    def extract_path(self) -> List[GridPoint]:
        if self.get_rhs(self.current_position) == float("inf"):
            return []

        path = [self.current_position]
        current = self.current_position
        visited = {current}

        while current != self.goal:
            best_next = None
            best_cost = float("inf")

            for neighbor in self.get_neighbors(current):
                if neighbor in visited:
                    continue

                candidate_cost = self.transition_cost(current, neighbor) + self.get_g(neighbor)

                if candidate_cost < best_cost:
                    best_cost = candidate_cost
                    best_next = neighbor

            if best_next is None or best_cost == float("inf"):
                return []

            path.append(best_next)
            current = best_next
            visited.add(current)

        return path

    def calculate_path_cost(self, path: List[GridPoint]) -> float:
        if len(path) < 2:
            return 0.0

        total = 0.0

        for a, b in zip(path, path[1:]):
            total += self.transition_cost(a, b)

        return float(total)


def run_dstar_lite(
    cost_matrix: np.ndarray,
    start_xy: Tuple[int, int],
    goal_xy: Tuple[int, int],
    flight_z: int,
    threat_threshold: float = 999999.0,
    fuel_capacity: Optional[float] = None,
) -> Dict[str, Any]:
    """
    Pipeline-friendly D* Lite entry point.

    Input convention:
    - start_xy = (x, y)
    - goal_xy = (x, y)

    Internal NumPy convention:
    - row = y
    - col = x
    """

    start_time = time.perf_counter()

    start_row_col = (start_xy[1], start_xy[0])
    goal_row_col = (goal_xy[1], goal_xy[0])

    try:
        planner = DStarLitePlanner(
            cost_matrix=cost_matrix,
            start=start_row_col,
            goal=goal_row_col,
            threat_threshold=threat_threshold,
        )

        if planner.is_blocked(*start_row_col):
            raise ValueError("Start point is blocked or above threat threshold")

        if planner.is_blocked(*goal_row_col):
            raise ValueError("Goal point is blocked or above threat threshold")

        planner.compute_shortest_path()
        path_row_col = planner.extract_path()

        runtime_seconds = time.perf_counter() - start_time

        if not path_row_col:
            return {
                "algorithm": "dstar-lite",
                "displayName": "D* Lite",
                "status": "failed",
                "success": False,
                "runtimeMs": runtime_seconds * 1000.0,
                "totalCost": 0.0,
                "nodesTraversed": 0,
                "nodesVisited": planner.nodes_visited,
                "pathNodeCount": 0,
                "path": [],
                "failureReason": "No feasible path found",
                "pathCsv": "dstar_lite_path.csv",
                "pathPlot": "dstar_lite_path.png",
            }

        total_cost = planner.calculate_path_cost(path_row_col)

        if fuel_capacity is not None and total_cost > fuel_capacity:
            return {
                "algorithm": "dstar-lite",
                "displayName": "D* Lite",
                "status": "failed",
                "success": False,
                "runtimeMs": runtime_seconds * 1000.0,
                "totalCost": total_cost,
                "nodesTraversed": len(path_row_col),
                "nodesVisited": planner.nodes_visited,
                "pathNodeCount": len(path_row_col),
                "path": [],
                "failureReason": "Path exceeds fuel capacity",
                "pathCsv": "dstar_lite_path.csv",
                "pathPlot": "dstar_lite_path.png",
            }

        path_xy = [
            {
                "x": col,
                "y": row,
                "z": flight_z,
            }
            for row, col in path_row_col
        ]

        return {
            "algorithm": "dstar-lite",
            "displayName": "D* Lite",
            "status": "completed",
            "success": True,
            "runtimeMs": runtime_seconds * 1000.0,
            "totalCost": total_cost,
            "nodesTraversed": len(path_xy),
            "nodesVisited": planner.nodes_visited,
            "pathNodeCount": len(path_xy),
            "path": path_xy,
            "failureReason": None,
            "pathCsv": "dstar_lite_path.csv",
            "pathPlot": "dstar_lite_path.png",
        }

    except Exception as exc:
        runtime_seconds = time.perf_counter() - start_time

        return {
            "algorithm": "dstar-lite",
            "displayName": "D* Lite",
            "status": "failed",
            "success": False,
            "runtimeMs": runtime_seconds * 1000.0,
            "totalCost": 0.0,
            "nodesTraversed": 0,
            "nodesVisited": 0,
            "pathNodeCount": 0,
            "path": [],
            "failureReason": str(exc),
            "pathCsv": "dstar_lite_path.csv",
            "pathPlot": "dstar_lite_path.png",
        }