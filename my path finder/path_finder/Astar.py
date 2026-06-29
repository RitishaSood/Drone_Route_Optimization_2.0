import heapq
import numpy as np
import matplotlib.pyplot as plt
from typing import List, Tuple, Optional, Dict

class ThreatAwarePathPlanner:
    """
    A path planning framework for surveillance drones operating in contested 
    environments. Employs a fuel-constrained A* algorithm over a custom 
    battlefield cost matrix.
    """
    def __init__(self, cost_matrix: np.ndarray, heuristic_type: str = 'manhattan'):
        """
        Initializes the planner with a cost matrix and a heuristic configuration.
        
        :param cost_matrix: 2D numpy array where each cell value represents 
                            the fuel/risk cost to enter that cell.
        :param heuristic_type: 'manhattan' or 'euclidean'
        """
        self.cost_matrix = cost_matrix
        self.rows, self.cols = cost_matrix.shape
        self.heuristic_type = heuristic_type.lower()
        
        # Define 8-directional movement vectors (dx, dy)
        self.movements = [
            (-1, 0),  # Up
            (1, 0),   # Down
            (0, -1),  # Left
            (0, 1),   # Right
            (-1, -1), # Diagonal Up-Left
            (-1, 1),  # Diagonal Up-Right
            (1, -1),  # Diagonal Down-Left
            (1, 1)    # Diagonal Down-Right
        ]

    def _calculate_heuristic(self, current: Tuple[int, int], goal: Tuple[int, int]) -> float:
        """
        Calculates the estimated cost from current position to the goal.
        Easily extensible for custom research metrics.
        """
        x1, y1 = current
        x2, y2 = goal
        
        if self.heuristic_type == 'manhattan':
            return abs(x1 - x2) + abs(y1 - y2)
        elif self.heuristic_type == 'euclidean':
            return np.sqrt((x1 - x2)**2 + (y1 - y2)**2)
        else:
            raise ValueError(f"Unknown heuristic type: {self.heuristic_type}")

    def plan_path(self, start: Tuple[int, int], goal: Tuple[int, int], fuel_capacity: float) -> Optional[Dict]:
        """
        Executes the fuel-constrained A* pathfinding algorithm.
        
        :param start: (x, y) start coordinate
        :param goal: (x, y) goal coordinate
        :param fuel_capacity: Maximum allowable cumulative movement cost
        :return: Dictionary containing optimization results or None if no path found.
        """
        # Boundary validation
        for point, name in [(start, "Start"), (goal, "Goal")]:
            if not (0 <= point[0] < self.rows and 0 <= point[1] < self.cols):
                raise ValueError(f"{name} position {point} is out of matrix boundaries.")

        # Priority Queue elements: (f_cost, g_cost, current_node)
        # Using g_cost as a tie-breaker or tracking variable
        open_list = []
        
        # Track historical progression for backtracking: child -> parent
        came_from = {}
        
        # Track best g-scores (min fuel used to reach a cell)
        g_score = {start: 0.0}
        
        # Calculate initial heuristic
        h_start = self._calculate_heuristic(start, goal)
        heapq.heappush(open_list, (h_start, 0.0, start))
        
        # Metrics tracking
        nodes_explored = 0
        closed_set = set()

        while open_list:
            f_current, g_current, current = heapq.heappop(open_list)
            nodes_explored += 1

            # Goal Check
            if current == goal:
                return self._reconstruct_path(came_from, current, start, fuel_capacity, nodes_explored)

            closed_set.add(current)

            # Explore Neighbors
            for dx, dy in self.movements:
                neighbor = (current[0] + dx, current[1] + dy)
                
                # 1. Boundary Verification
                if not (0 <= neighbor[0] < self.rows and 0 <= neighbor[1] < self.cols):
                    continue
                
                # 2. Closed Set Skip
                if neighbor in closed_set:
                    continue

                # 3. Dynamic Cost/Fuel Calculation
                # Moving into the neighbor cell consumes fuel equal to its cost value
                step_fuel = self.cost_matrix[neighbor[0], neighbor[1]]
                tentative_g_score = g_current + step_fuel

                # 4. Fuel Constraint Pruning
                if tentative_g_score > fuel_capacity:
                    continue  # Route is unfeasible due to fuel depletion

                # 5. Optimization Check
                if tentative_g_score < g_score.get(neighbor, float('inf')):
                    came_from[neighbor] = current
                    g_score[neighbor] = tentative_g_score
                    f_score = tentative_g_score + self._calculate_heuristic(neighbor, goal)
                    heapq.heappush(open_list, (f_score, tentative_g_score, neighbor))

        # Open list empty without finding goal
        return None

    def _reconstruct_path(self, came_from: Dict, current: Tuple[int, int], start: Tuple[int, int], 
                           fuel_capacity: float, nodes_explored: int) -> Dict:
        """Helper method to compile metrics and reverse path tracking."""
        path = [current]
        while current in came_from:
            current = came_from[current]
            path.append(current)
        path.reverse()

        # Compute accurate execution metrics
        # The cost of the start cell is omitted if the drone is deployed *at* that location safely.
        # This implementation counts the cost of entering every node after deployment.
        total_cost = sum(self.cost_matrix[node[0], node[1]] for node in path if node != start)

        return {
            "path": path,
            "total_path_cost": total_cost,
            "fuel_consumed": total_cost,
            "remaining_fuel": fuel_capacity - total_cost,
            "nodes_explored": nodes_explored,
            "path_length": len(path)
        }

    def visualize_mission(self, result: Optional[Dict], start: Tuple[int, int], goal: Tuple[int, int]):
        """
        Visualizes the battlefield cost matrix heatmap and overlays the calculated route.
        """
        plt.figure(figsize=(10, 8))
        
        # Display cost layer map
        plt.imshow(self.cost_matrix, cmap='YlOrRd', origin='upper')
        cbar = plt.colorbar()
        cbar.set_label('Threat Index / Fuel Cost per Unit Cell', rotation=270, labelpad=15)

        # Plot Start/Goal landmarks
        plt.scatter(start[1], start[0], color='blue', marker='P', s=150, label='Start Node (Drone Launch)', zorder=5)
        plt.scatter(goal[1], goal[0], color='green', marker='X', s=150, label='Goal Node (Target Obj)', zorder=5)

        if result and result["path"]:
            path = np.array(result["path"])
            # In image space, x matches columns (index 1) and y matches rows (index 0)
            plt.plot(path[:, 1], path[:, 0], color='cyan', linewidth=2.5, label='Optimized Safe Route', zorder=4)
            plt.title(f"A* Threat-Aware Path Optimization\nFuel Consumed: {result['fuel_consumed']:.1f} | Nodes Explored: {result['nodes_explored']}", fontsize=12)
        else:
            plt.title("A* Route Planning Failed: Fuel Capacity Insufficient for Mission Parameters", color='red', fontsize=12)

        plt.xlabel("Grid Column Axis (Y)")
        plt.ylabel("Grid Row Axis (X)")
        plt.legend(loc='upper right')
        plt.grid(True, alpha=0.15)
        plt.show()

# ==========================================
# Run Sample Simulation Environment
# ==========================================
if __name__ == "__main__":
    # Fix seed for reproducible battlefield matrix generation
    np.random.seed(42)
    
    GRID_SIZE = 100
    
    # Generate background threat matrix (values between 1.0 baseline and 15.0 high-risk zones)
    # We add a few Gaussian-like high threat blobs to mimic simulated radar or anti-air sites
    base_matrix = np.random.uniform(1.0, 5.0, size=(GRID_SIZE, GRID_SIZE))
    
    # Injecting synthetic local threat features
    x, y = np.mgrid[0:GRID_SIZE, 0:GRID_SIZE]
    threat_blob_1 = 30 * np.exp(-((x - 45)**2 + (y - 45)**2) / 200)
    threat_blob_2 = 25 * np.exp(-((x - 70)**2 + (y - 25)**2) / 150)
    battlefield_costs = base_matrix + threat_blob_1 + threat_blob_2

    # Mission Settings
    start_pos = (5, 5)
    goal_pos = (90, 90)
    allocated_fuel = 450.0  # Try adjusting this to observe safe path alterations vs failures

    print("Initializing Battlefield Environment Planner...")
    planner = ThreatAwarePathPlanner(cost_matrix=battlefield_costs, heuristic_type='euclidean')
    
    print(f"Executing Pathfinding from {start_pos} to {goal_pos}...")
    mission_summary = planner.plan_path(start=start_pos, goal=goal_pos, fuel_capacity=allocated_fuel)

    if mission_summary:
        print("\n--- OPTIMAL MISSION PROFILE FOUND ---")
        print(f"Status:            Success")
        print(f"Path Length:       {mission_summary['path_length']} nodes")
        print(f"Total Fuel Cost:   {mission_summary['total_path_cost']:.2f} units")
        print(f"Remaining Fuel:    {mission_summary['remaining_fuel']:.2f} units")
        print(f"Search Efficiency: {mission_summary['nodes_explored']} spaces analyzed")
    else:
        print("\n--- MISSION CRITICAL ERROR ---")
        print("Status: Terminated. No viable path matches current fuel or survivability parameters.")

    # Render Visual Plot
    planner.visualize_mission(mission_summary, start=start_pos, goal=goal_pos)