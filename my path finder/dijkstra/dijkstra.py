import time
import math
import heapq
import numpy as np
import matplotlib.pyplot as plt
from typing import List, Tuple, Dict, Any

class BattlefieldGrid:
    """Manages the 2D battlefield environment, movement dynamics, and constraints."""
    def __init__(self, cost_matrix: np.ndarray, threat_threshold: float):
        self.cost_matrix = cost_matrix
        self.rows, self.cols = cost_matrix.shape
        self.threat_threshold = threat_threshold
        
        # 8-directional movements: (dx, dy, distance_multiplier)
        self.movements = [
            (0, 1, 1.0), (1, 0, 1.0), (0, -1, 1.0), (-1, 0, 1.0),
            (1, 1, math.sqrt(2)), (-1, 1, math.sqrt(2)), 
            (1, -1, math.sqrt(2)), (-1, -1, math.sqrt(2))
        ]

    def is_valid(self, r: int, c: int) -> bool:
        return 0 <= r < self.rows and 0 <= c < self.cols

    def get_neighbors(self, r: int, c: int) -> List[Tuple[int, int, float]]:
        neighbors = []
        for dr, dc, move_mult in self.movements:
            nr, nc = r + dr, c + dc
            if self.is_valid(nr, nc):
                cell_cost = self.cost_matrix[nr, nc]
                
                # Dynamic Check: Abort if cell exceeds the maximum allowed threat threshold
                if cell_cost >= self.threat_threshold or np.isinf(cell_cost):
                    continue
                
                transition_cost = move_mult * cell_cost
                neighbors.append((nr, nc, transition_cost))
        return neighbors

class ThreatAwarePathPlanner:
    """Executes fuel and threat-constrained Dijkstra path planning."""
    def __init__(self, grid: BattlefieldGrid):
        self.grid = grid

    def plan_dijkstra(self, start: Tuple[int, int], goal: Tuple[int, int], fuel_capacity: float) -> Dict[str, Any]:
        start_time = time.perf_counter()
        
        # Priority Queue: (accumulated_cost, row, col)
        pq = [(0.0, start[0], start[1])]
        
        distances = np.full((self.grid.rows, self.grid.cols), np.inf)
        distances[start[0], start[1]] = 0.0
        
        parent_map = {}
        visited = set()
        nodes_expanded = 0
        success = False

        while pq:
            curr_cost, r, c = heapq.heappop(pq)
            
            if curr_cost > distances[r, c] or (r, c) in visited:
                continue
            
            visited.add((r, c))
            nodes_expanded += 1

            if (r, c) == goal:
                success = True
                break

            for nr, nc, transition_cost in self.grid.get_neighbors(r, c):
                next_cost = curr_cost + transition_cost
                
                # Hard Constraint: Reject paths exceeding fuel budget
                if next_cost > fuel_capacity:
                    continue
                
                if next_cost < distances[nr, nc]:
                    distances[nr, nc] = next_cost
                    parent_map[(nr, nc)] = (r, c)
                    heapq.heappush(pq, (next_cost, nr, nc))

        runtime = time.perf_counter() - start_time
        
        # Path reconstruction
        path = []
        if success:
            curr = goal
            while curr != start:
                path.append(curr)
                curr = parent_map[curr]
            path.append(start)
            path.reverse()
            total_cost = distances[goal[0], goal[1]]
        else:
            total_cost = 0.0

        return {
            "success": success,
            "path": path,
            "total_cost": total_cost,
            "fuel_consumed": total_cost,
            "nodes_expanded": nodes_expanded,
            "runtime_seconds": runtime
        }

# ==========================================
# SIMULATION EXECUTION
# ==========================================

def generate_synthetic_battlefield(rows: int, cols: int, seed: int = 42) -> np.ndarray:
    """Generates continuous risk landscape with overlapping threat zones."""
    np.random.seed(seed)
    grid = np.full((rows, cols), 1.0) # Base terrain cost
    
    # Inject localized hazard peaks (e.g., radar, SAM bubbles)
    num_threats = 6
    for _ in range(num_threats):
        center_r, center_c = np.random.randint(0, rows), np.random.randint(0, cols)
        intensity = np.random.uniform(20.0, 45.0)
        radius = np.random.uniform(10.0, 22.0)
        
        for r in range(rows):
            for c in range(cols):
                dist_sq = (r - center_r)**2 + (c - center_c)**2
                grid[r, c] += intensity * math.exp(-dist_sq / (2 * (radius**2)))
                
    return grid

def run_simulation():
    # Environment Setup
    GRID_SIZE = (100, 100)
    START_POS = (10, 10)
    GOAL_POS = (90, 90)
    FUEL_BUDGET = 500.0  
    
    # --- THREAT CONFIGURATION VARIABLE ---
    # Cells with a cost equal to or higher than this value are treated as impassable/lethal.
    # Adjust this value to calibrate risk tolerance for your research.
    THREAT_THRESHOLD = 30.0 
    
    # Generate Environment
    cost_matrix = generate_synthetic_battlefield(GRID_SIZE[0], GRID_SIZE[1], seed=101)
    
    # Initialize Engine
    battlefield = BattlefieldGrid(cost_matrix, threat_threshold=THREAT_THRESHOLD)
    planner = ThreatAwarePathPlanner(battlefield)
    
    # Run Router
    metrics = planner.plan_dijkstra(START_POS, GOAL_POS, FUEL_BUDGET)

    total_cells_covered = len(metrics['path'])
    total_fuel_consumed = metrics['fuel_consumed']
    mission_success = metrics['success']
    
    # ==========================================
    # REQUESTED RESEARCH OUTPUTS
    # ==========================================
    print("\n" + "="*45)
    print("             MISSION SUMMARY")
    print("="*45)
    print(f"Total Cells Covered (Path Length): {total_cells_covered}")
    print(f"Total Fuel Consumed:               {total_fuel_consumed:.2f} units")
    print(f"Mission Success:                   {'SUCCESS' if mission_success else 'FAILED'}")
    print("="*45)
    
    # Extended Benchmarking Diagnostics
    print(f"Total Nodes Expanded:              {metrics['nodes_expanded']}")
    print(f"Execution Runtime:                 {metrics['runtime_seconds']:.4f} seconds\n")

    # Map Visualization
    if metrics['success']:
        path_coords = np.array(metrics['path'])
        fig, ax = plt.subplots(figsize=(10, 8))
        
        cmap = ax.imshow(cost_matrix, cmap='YlOrRd', origin='upper', vmax=THREAT_THRESHOLD)
        cbar = fig.colorbar(cmap, ax=ax)
        cbar.set_label('Threat Risk Level', rotation=270, labelpad=15)
        
        ax.plot(path_coords[:, 1], path_coords[:, 0], color='cyan', linewidth=3, label="Optimal Route")
        ax.scatter(START_POS[1], START_POS[0], color='lime', marker='^', s=150, edgecolors='black', label="Start")
        ax.scatter(GOAL_POS[1], GOAL_POS[0], color='magenta', marker='X', s=150, edgecolors='black', label="Goal")
        
        ax.set_title("UAV Threat-Aware Path Planning Optimization", fontsize=12, fontweight='bold')
        ax.legend(loc='lower right')
        ax.grid(True, alpha=0.2)
        plt.tight_layout()
        plt.show()

if __name__ == "__main__":
    run_simulation()
