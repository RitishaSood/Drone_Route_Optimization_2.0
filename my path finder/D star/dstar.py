import numpy as np
import heapq
import time
import matplotlib.pyplot as plt
from typing import List, Tuple, Dict, Set, Optional

class PriorityQueue:
    def __init__(self):
        self.heap = []
        self.vertices = {}

    def insert(self, vertex: Tuple[int, int], key: Tuple[float, float]):
        if vertex in self.vertices:
            self.update(vertex, key)
            return
        entry = [key[0], key[1], vertex]
        self.vertices[vertex] = entry
        heapq.heappush(self.heap, entry)

    def remove(self, vertex: Tuple[int, int]):
        if vertex in self.vertices:
            entry = self.vertices.pop(vertex)
            entry[-1] = None

    def pop(self) -> Optional[Tuple[Tuple[int, int], Tuple[float, float]]]:
        while self.heap:
            k0, k1, vertex = heapq.heappop(self.heap)
            if vertex is not None:
                del self.vertices[vertex]
                return vertex, (k0, k1)
        return None

    def top_key(self) -> Tuple[float, float]:
        while self.heap:
            k0, k1, vertex = self.heap[0]
            if vertex is not None:
                return (k0, k1)
            heapq.heappop(self.heap)
        return (float('inf'), float('inf'))

    def update(self, vertex: Tuple[int, int], new_key: Tuple[float, float]):
        if vertex in self.vertices:
            self.remove(vertex)
        self.insert(vertex, new_key)

    def contains(self, vertex: Tuple[int, int]) -> bool:
        return vertex in self.vertices


class DStarLiteUAV:
    def __init__(self, cost_matrix: np.ndarray, start: Tuple[int, int], goal: Tuple[int, int], fuel_capacity: float):
        self.cost_matrix = cost_matrix
        self.rows, self.cols = cost_matrix.shape
        self.start = start
        self.current_position = start
        self.goal = goal
        self.fuel_capacity = fuel_capacity

        self.g = {}
        self.rhs = {}
        self.km = 0.0
        self.s_last = self.start
        self.U = PriorityQueue()
        
        self.metrics = {"initial_time": 0.0, "replanning_time": 0.0, "nodes_expanded": 0, "nodes_updated": 0}
        self.initialize()

    def initialize(self):
        self.rhs[self.goal] = 0.0
        self.U.insert(self.goal, self.calculate_key(self.goal))

    def get_g(self, s: Tuple[int, int]) -> float:
        return self.g.get(s, float('inf'))

    def get_rhs(self, s: Tuple[int, int]) -> float:
        return self.rhs.get(s, float('inf'))

    def heuristic(self, s1: Tuple[int, int], s2: Tuple[int, int]) -> float:
        dx, dy = abs(s1[0] - s2[0]), abs(s1[1] - s2[1])
        return min(dx, dy) * np.sqrt(2) + abs(dx - dy)

    def calculate_key(self, s: Tuple[int, int]) -> Tuple[float, float]:
        g_rhs = min(self.get_g(s), self.get_rhs(s))
        return (g_rhs + self.heuristic(self.current_position, s) + self.km, g_rhs)

    def get_neighbors(self, s: Tuple[int, int]) -> List[Tuple[int, int]]:
        neighbors = []
        directions = [(-1,0), (1,0), (0,-1), (0,1), (-1,-1), (-1,1), (1,-1), (1,1)]
        for dx, dy in directions:
            nx, ny = s[0] + dx, s[1] + dy
            if 0 <= nx < self.rows and 0 <= ny < self.cols:
                neighbors.append((nx, ny))
        return neighbors

    def transition_cost(self, s1: Tuple[int, int], s2: Tuple[int, int]) -> float:
        step_dist = np.sqrt(2) if (s1[0] != s2[0] and s1[1] != s2[1]) else 1.0
        avg_multiplier = (self.cost_matrix[s1[0], s1[1]] + self.cost_matrix[s2[0], s2[1]]) / 2.0
        return step_dist * avg_multiplier

    def update_vertex(self, u: Tuple[int, int]):
        self.metrics["nodes_updated"] += 1
        if u != self.goal:
            self.rhs[u] = min(self.transition_cost(u, s_prime) + self.get_g(s_prime) for s_prime in self.get_neighbors(u))
        if self.U.contains(u): self.U.remove(u)
        if self.get_g(u) != self.get_rhs(u): self.U.insert(u, self.calculate_key(u))

    def compute_shortest_path(self):
        while (self.U.top_key() < self.calculate_key(self.current_position) or 
               self.get_rhs(self.current_position) != self.get_g(self.current_position)):
            k_old = self.U.top_key()
            u, _ = self.U.pop() or (None, None)
            if u is None: break
            
            self.metrics["nodes_expanded"] += 1
            if k_old < self.calculate_key(u):
                self.U.insert(u, self.calculate_key(u))
            elif self.get_g(u) > self.get_rhs(u):
                self.g[u] = self.get_rhs(u)
                for s_prime in self.get_neighbors(u): self.update_vertex(s_prime)
            else:
                self.g[u] = float('inf')
                self.update_vertex(u)
                for s_prime in self.get_neighbors(u): self.update_vertex(s_prime)

    def extract_path(self) -> List[Tuple[int, int]]:
        path = [self.current_position]
        curr = self.current_position
        visited = {curr}
        while curr != self.goal:
            best_next, min_cost = None, float('inf')
            for n in self.get_neighbors(curr):
                if n in visited: continue
                cost = self.transition_cost(curr, n) + self.get_g(n)
                if cost < min_cost:
                    min_cost, best_next = cost, n
            if best_next is None or min_cost == float('inf'): return []
            path.append(best_next)
            curr = best_next
            visited.add(curr)
        return path

    def plan_initial_route(self) -> List[Tuple[int, int]]:
        t0 = time.time()
        self.compute_shortest_path()
        self.metrics["initial_time"] = time.time() - t0
        return self.extract_path()

    def apply_battlefield_updates(self, changes: Dict[Tuple[int, int], float]) -> List[Tuple[int, int]]:
        t0 = time.time()
        self.km += self.heuristic(self.s_last, self.current_position)
        self.s_last = self.current_position
        affected = set()
        for (x, y), new_cost in changes.items():
            self.cost_matrix[x, y] = new_cost
            affected.add((x, y))
            for n in self.get_neighbors((x, y)): affected.add(n)
        for u in affected: self.update_vertex(u)
        self.compute_shortest_path()
        self.metrics["replanning_time"] = time.time() - t0
        return self.extract_path()


# --- Environment Generators ---
def generate_battlefield(w: int, h: int) -> np.ndarray:
    grid = np.ones((w, h))
    x, y = np.meshgrid(np.arange(w), np.arange(h), indexing='ij')
    grid += 15.0 * np.exp(-((x - 30)**2 + (y - 40)**2) / (2 * 12**2))  # Radar 1
    grid += 25.0 * np.exp(-((x - 70)**2 + (y - 65)**2) / (2 * 10**2))  # Radar 2
    return grid

def simulate_threat(grid: np.ndarray, center: Tuple[int, int], r: int) -> Dict[Tuple[int, int], float]:
    changes = {}
    for i in range(max(0, center[0]-r), min(grid.shape[0], center[0]+r)):
        for j in range(max(0, center[1]-r), min(grid.shape[1], center[1]+r)):
            if np.sqrt((i-center[0])**2 + (j-center[1])**2) <= r:
                changes[(i, j)] = grid[i, j] + 35.0  # Spike cost significantly
    return changes


# =====================================================================
# SIMULATION EXECUTION & EXTRACTION INTERFACE
# =====================================================================
if __name__ == "__main__":
    # --- Configurable Parameters ---
    GRID_SIZE = 100
    START = (10, 10)
    GOAL = (90, 90)
    FUEL_BUDGET = 500.0
    
    # User-defined danger threshold: Any grid step cost >= this value fails the mission.
    MAX_CELL_COST_THRESHOLD = 30.0  

    # 1. Initialize System
    cost_map = generate_battlefield(GRID_SIZE, GRID_SIZE)
    planner = DStarLiteUAV(cost_map, START, GOAL, FUEL_BUDGET)
    
    # 2. Initial Global Plan
    initial_path = planner.plan_initial_route()
    
    # 3. Simulate Dynamic SAM Threat directly breaking the initial path
    mid_node = initial_path[len(initial_path) // 2]
    threat_changes = simulate_threat(cost_map, center=mid_node, r=6)
    
    # 4. Incremental Re-route Execution
    final_path = planner.apply_battlefield_updates(threat_changes)

    # =====================================================================
    # HOW TO GET FUEL CONSUMED, CELLS COVERED, AND MISSION SUCCESS STATUS
    # =====================================================================
    # These metrics are explicitly calculated below and mapped to easy variables:
    
    total_cells_covered = len(final_path)
    total_fuel_consumed = 0.0
    max_cost_encountered = 0.0
    
    if total_cells_covered > 0:
        # Calculate strict step-by-step cost accumulation
        for i in range(total_cells_covered - 1):
            s1 = final_path[i]
            s2 = final_path[i+1]
            total_fuel_consumed += planner.transition_cost(s1, s2)
            
            # Keep track of the highest threat cell the drone stepped into
            max_cost_encountered = max(max_cost_encountered, cost_map[s2[0], s2[1]])

        # Evaluate constraints logically
        if total_fuel_consumed > FUEL_BUDGET:
            mission_success = "FAILED: Fuel Capacity Exhausted"
        elif max_cost_encountered >= MAX_CELL_COST_THRESHOLD:
            mission_success = f"FAILED: Exceeded Safe Threat Threshold ({max_cost_encountered:.2f} >= {MAX_CELL_COST_THRESHOLD})"
        else:
            mission_success = "SUCCESS"
    else:
        total_cells_covered = 0
        total_fuel_consumed = 0.0
        mission_success = "FAILED: No valid path found"

    # --- Print Outputs ---
    print("\n" + "="*40)
    print("         EXTRACTED MISSION LOGS")
    print("="*40)
    print(f"Total Cells Covered : {total_cells_covered}")
    print(f"Total Fuel Consumed : {total_fuel_consumed:.2f} / {FUEL_BUDGET}")
    print(f"Mission Success     : {mission_success}")
    print("="*40)

    # --- Render Visual Outputs ---
    fig, ax = plt.subplots(figsize=(7, 6))
    ax.imshow(cost_map.T, origin='lower', cmap='jet', alpha=0.8)
    if final_path:
        fx, fy = zip(*final_path)
        ax.plot(fx, fy, color='white', linewidth=3, label='Final Repaired Route')
    ax.scatter(*START, color='lime', marker='^', s=150, label='Start')
    ax.scatter(*GOAL, color='magenta', marker='X', s=150, label='Goal')
    ax.set_title(f"Dynamic D* Lite Path\nStatus: {mission_success}")
    ax.legend()
    plt.show()