import time
import random
import numpy as np
import matplotlib.pyplot as plt
from typing import List, Tuple, Dict, Any

class BattlefieldGrid:
    def __init__(self, matrix: np.ndarray):
        self.matrix = matrix
        self.height, self.width = matrix.shape

    def is_valid_coordinate(self, x: int, y: int) -> bool:
        return 0 <= x < self.width and 0 <= y < self.height

    def get_neighbors(self, x: int, y: int) -> List[Tuple[int, int, float]]:
        neighbors = []
        # 8-directional offsets: (dx, dy, step_distance)
        directions = [
            (0, -1, 1.0), (0, 1, 1.0), (-1, 0, 1.0), (1, 0, 1.0),
            (-1, -1, 1.4142), (-1, 1, 1.4142), (1, -1, 1.4142), (1, 1, 1.4142)
        ]
        for dx, dy, dist in directions:
            nx, ny = x + dx, y + dy
            if self.is_valid_coordinate(nx, ny):
                neighbors.append((nx, ny, dist))
        return neighbors

    def calculate_step_cost(self, x2: int, y2: int, dist: float) -> float:
        # Movement Distance * Destination Cell Base Cost
        return dist * self.matrix[y2, x2]


class AntColonyRoutePlanner:
    def __init__(self, 
                 grid: BattlefieldGrid, 
                 start: Tuple[int, int], 
                 goal: Tuple[int, int],
                 num_ants: int = 30,
                 iterations: int = 50,
                 alpha: float = 1.0,
                 beta: float = 2.0,
                 rho: float = 0.1,
                 Q: float = 100.0,
                 fuel_capacity: float = 500.0,
                 max_path_length: int = 300,
                 threat_threshold: float = 12.0): # Over this cost cell = path failure
        
        self.grid = grid
        self.start = start
        self.goal = goal
        self.num_ants = num_ants
        self.iterations = iterations
        self.alpha = alpha  
        self.beta = beta    
        self.rho = rho      
        self.Q = Q          
        self.fuel_capacity = fuel_capacity
        self.max_path_length = max_path_length
        self.threat_threshold = threat_threshold
        
        self.pheromones = np.full((grid.height, grid.width), 1.0, dtype=float)
        self.best_path = None
        self.best_cost = float('inf')
        self.best_fuel_consumed = 0.0
        self.convergence_history = []

    def _get_heuristic(self, x: int, y: int, dist: float) -> float:
        cost = self.grid.calculate_step_cost(x, y, dist)
        return 1.0 / (cost + 1e-6)

    def _construct_ant_path(self) -> Tuple[List[Tuple[int, int]], float, bool]:
        path = [self.start]
        visited = {self.start}
        current_fuel = self.fuel_capacity
        total_cost = 0.0
        
        while path[-1] != self.goal:
            cx, cy = path[-1]
            neighbors = self.grid.get_neighbors(cx, cy)
            unvisited = [(nx, ny, dist) for nx, ny, dist in neighbors if (nx, ny) not in visited]
            
            if not unvisited:
                return path, total_cost, False # Dead end
            
            probabilities = []
            valid_candidates = []
            
            for nx, ny, dist in unvisited:
                # Check Threat Threshold restriction
                if self.grid.matrix[ny, nx] >= self.threat_threshold:
                    continue # Disallow paths entering critical risk zones
                    
                step_cost = self.grid.calculate_step_cost(nx, ny, dist)
                
                if current_fuel - step_cost >= 0:
                    tau = self.pheromones[ny, nx] ** self.alpha
                    eta = self._get_heuristic(nx, ny, dist) ** self.beta
                    probabilities.append(tau * eta)
                    valid_candidates.append((nx, ny, step_cost))
            
            if not valid_candidates:
                return path, total_cost, False # Out of fuel or blocked by threats
            
            prob_sum = sum(probabilities)
            probabilities = [p / prob_sum for p in probabilities] if prob_sum > 0 else [1.0/len(valid_candidates)] * len(valid_candidates)
                
            chosen_idx = random.choices(range(len(valid_candidates)), weights=probabilities, k=1)[0]
            next_x, next_y, step_cost = valid_candidates[chosen_idx]
            
            path.append((next_x, next_y))
            visited.add((next_x, next_y))
            current_fuel -= step_cost
            total_cost += step_cost
            
            if len(path) > self.max_path_length:
                return path, total_cost, False
                
        return path, total_cost, True

    def optimize(self) -> Dict[str, Any]:
        start_time = time.time()
        
        for iteration in range(self.iterations):
            iteration_paths = []
            iteration_costs = []
            
            for _ in range(self.num_ants):
                path, cost, success = self._construct_ant_path()
                if success:
                    iteration_paths.append(path)
                    iteration_costs.append(cost)
            
            # Pheromone Evaporation
            self.pheromones *= (1.0 - self.rho)
            
            # Pheromone Update
            for path, cost in zip(iteration_paths, iteration_costs):
                deposit = self.Q / cost
                for x, y in path:
                    self.pheromones[y, x] += deposit
            
            # Keep Track of Global Best Solution
            if iteration_costs:
                min_iter_cost = min(iteration_costs)
                if min_iter_cost < self.best_cost:
                    self.best_cost = min_iter_cost
                    self.best_path = iteration_paths[iteration_costs.index(min_iter_cost)]
                    self.best_fuel_consumed = min_iter_cost
            
            self.convergence_history.append(self.best_cost if self.best_cost != float('inf') else None)
            
        runtime = time.time() - start_time
        
        # --- NEW EASY EXTRACTION METRICS REQUIRED ---
        mission_success = self.best_path is not None
        total_cells_covered = len(self.best_path) if mission_success else 0
        total_fuel_consumed = self.best_fuel_consumed if mission_success else 0.0
        
        return {
            "mission_success": mission_success,
            "total_cells_covered": total_cells_covered,
            "total_fuel_consumed": total_fuel_consumed,
            "best_path": self.best_path,
            "best_cost": self.best_cost,
            "runtime": runtime,
            "convergence_history": self.convergence_history
        }


# ==========================================
# RUNNABLE EXAMPLE & EXTRACTION DEMO
# ==========================================

def generate_battlefield(width: int = 100, height: int = 100) -> np.ndarray:
    np.random.seed(42)
    grid = np.ones((height, width)) * 1.0
    threat_centers = [(25, 30, 15), (70, 40, 20), (45, 75, 18), (80, 80, 12)]
    
    for cx, cy, r in threat_centers:
        for y in range(height):
            for x in range(width):
                dist = np.sqrt((x - cx)**2 + (y - cy)**2)
                if dist <= r:
                    grid[y, x] += (1.0 - (dist / r)) * 15.0 # Max threat peaks at 16.0
                    
    grid += np.random.uniform(0.0, 2.0, size=(height, width))
    return grid

if __name__ == "__main__":
    # Environment Setup
    GRID_SIZE = 100
    START = (5, 5)
    GOAL = (95, 95)
    FUEL_LIMIT = 600.0
    
    # 1. DEFINE THRESHOLD VALUE VARIABLE HERE
    # If any cell cost >= THREAT_THRESHOLD, it's considered unpassable/fatal threat.
    THREAT_THRESHOLD = 11.5 
    
    cost_matrix = generate_battlefield(GRID_SIZE, GRID_SIZE)
    battlefield = BattlefieldGrid(cost_matrix)
    
    planner = AntColonyRoutePlanner(
        grid=battlefield, start=START, goal=GOAL,
        num_ants=25, iterations=40, alpha=1.2, beta=2.5, rho=0.15, Q=150.0,
        fuel_capacity=FUEL_LIMIT, max_path_length=350,
        threat_threshold=THREAT_THRESHOLD # Pass threshold variable to model
    )
    
    # Execute Optimizer
    results = planner.optimize()
    
    # 2. HOW TO EXTRACT THE THREE REQUIRED VALUES
    cells_covered = results["total_cells_covered"]
    fuel_used = results["total_fuel_consumed"]
    success_status = results["mission_success"]
    
    # Output to user terminal
    print("=" * 40)
    print("        EXTRACTION OUTPUT METRICS       ")
    print("=" * 40)
    print(f"Total Cells Covered: {cells_covered}")
    print(f"Total Fuel Consumed: {fuel_used:.2f}")
    print(f"Mission Success:     {success_status}")
    print("=" * 40)

    # Optional: Basic plotting block for verification
    if success_status:
        path_np = np.array(results['best_path'])
        plt.figure(figsize=(6, 5))
        plt.imshow(cost_matrix, cmap='yaml', origin='upper')
        plt.colorbar(label='Threat Cost')
        plt.plot(path_np[:, 0], path_np[:, 1], color='cyan', linewidth=2, label='ACO Path')
        plt.scatter([START[0], GOAL[0]], [START[1], GOAL[1]], color=['lime','red'], marker='o', s=100)
        plt.title('UAV ACO Route Verification')
        plt.legend()
        plt.show()