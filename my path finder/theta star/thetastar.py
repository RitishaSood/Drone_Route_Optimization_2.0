import time
import math
import heapq
import numpy as np
import matplotlib.pyplot as plt
from typing import List, Tuple, Dict, Set, Optional

class BattlefieldPathPlanner:
    """
    UAV Routing framework using A* and Theta* with a customizable threat threshold.
    """
    def __init__(self, cost_matrix: np.ndarray, fuel_capacity: float, threat_threshold: float):
        self.cost_matrix = cost_matrix
        self.height, self.width = cost_matrix.shape
        self.fuel_capacity = fuel_capacity
        self.threat_threshold = threat_threshold  # Cells above this cost are blocked
        
        # 8-Directional movement offsets and kinematic weights
        self.movements = [
            (0, 1, 1.0), (1, 0, 1.0), (0, -1, 1.0), (-1, 0, 1.0),
            (1, 1, math.sqrt(2)), (1, -1, math.sqrt(2)), 
            (-1, 1, math.sqrt(2)), (-1, -1, math.sqrt(2))
        ]

    def _euclidean_heuristic(self, node: Tuple[int, int], goal: Tuple[int, int]) -> float:
        return math.sqrt((node[0] - goal[0])**2 + (node[1] - goal[1])**2)

    def _is_valid(self, node: Tuple[int, int]) -> bool:
        x, y = node
        return 0 <= x < self.height and 0 <= y < self.width and self.cost_matrix[x, y] <= self.threat_threshold

    def bresenham_los_cost(self, start: Tuple[int, int], end: Tuple[int, int]) -> Tuple[bool, float]:
        """Checks straight-line visibility and calculates continuous path cost."""
        x0, y0 = start
        x1, y1 = end
        dx, dy = abs(x1 - x0), abs(y1 - y0)
        sx = 1 if x0 < x1 else -1
        sy = 1 if y0 < y1 else -1
        err = dx - dy
        
        total_cost = 0.0
        steps = 0
        curr_x, curr_y = x0, y0
        
        while True:
            if not self._is_valid((curr_x, curr_y)):
                return False, float('inf')
            
            total_cost += self.cost_matrix[curr_x, curr_y]
            steps += 1
            
            if curr_x == x1 and curr_y == y1:
                break
                
            e2 = 2 * err
            if e2 > -dy:
                err -= dy
                curr_x += sx
            if e2 < dx:
                err += dx
                curr_y += sy
                
        actual_dist = math.sqrt((x1 - x0)**2 + (y1 - y0)**2)
        if steps > 0:
            total_cost = (total_cost / steps) * actual_dist
        return True, total_cost

    def solve(self, start: Tuple[int, int], goal: Tuple[int, int], use_theta_star: bool = True) -> Dict:
        if not self._is_valid(start) or not self._is_valid(goal):
            return {"success": False, "msg": "Mission Failed: Start/Goal in lethal threat zone.", "path": np.array([]), "fuel_consumed": float('inf'), "cells_covered": 0}

        open_set = []
        heapq.heappush(open_set, (0.0, start))
        
        parents = {start: start}
        g_score = {start: 0.0}
        f_score = {start: self._euclidean_heuristic(start, goal)}
        explored_nodes = set()
        los_optimizations = 0

        while open_set:
            _, current = heapq.heappop(open_set)
            
            if current == goal:
                path = []
                curr = goal
                while curr != start:
                    path.append(curr)
                    curr = parents[curr]
                path.append(start)
                path.reverse()
                
                fuel_consumed = g_score[goal]
                path_length = sum(math.sqrt((path[i+1][0] - path[i][0])**2 + (path[i+1][1] - path[i][1])**2) for i in range(len(path) - 1))
                
                return {
                    "success": True,
                    "path": np.array(path),
                    "fuel_consumed": fuel_consumed,
                    "remaining_fuel": self.fuel_capacity - fuel_consumed,
                    "path_length": path_length,
                    "explored_nodes": len(explored_nodes),
                    "cells_covered": len(path),
                    "los_optimizations": los_optimizations,
                    "msg": "Mission Success: Target Reached."
                }

            if current in explored_nodes:
                continue
            explored_nodes.add(current)

            for dx, dy, move_cost in self.movements:
                neighbor = (current[0] + dx, current[1] + dy)
                if not self._is_valid(neighbor) or neighbor in explored_nodes:
                    continue

                edge_cost = self.cost_matrix[neighbor] * move_cost
                
                if use_theta_star:
                    parent_node = parents[current]
                    has_los, los_cost = self.bresenham_los_cost(parent_node, neighbor)
                    if has_los and (g_score[parent_node] + los_cost < g_score[current] + edge_cost):
                        tentative_g = g_score[parent_node] + los_cost
                        tentative_parent = parent_node
                        is_optimized = True
                    else:
                        tentative_g = g_score[current] + edge_cost
                        tentative_parent = current
                        is_optimized = False
                else:
                    tentative_g = g_score[current] + edge_cost
                    tentative_parent = current
                    is_optimized = False

                if tentative_g > self.fuel_capacity:
                    continue

                if neighbor not in g_score or tentative_g < g_score[neighbor]:
                    g_score[neighbor] = tentative_g
                    f_score[neighbor] = tentative_g + self._euclidean_heuristic(neighbor, goal)
                    parents[neighbor] = tentative_parent
                    if is_optimized: los_optimizations += 1
                    heapq.heappush(open_set, (f_score[neighbor], neighbor))

        return {
            "success": False,
            "msg": "Mission Failed: No viable route found (Fuel limit or threat blockage).",
            "path": np.array([]),
            "fuel_consumed": float('inf'),
            "cells_covered": 0,
            "explored_nodes": len(explored_nodes)
        }

def generate_battlefield(size: int = 100) -> np.ndarray:
    np.random.seed(42)
    terrain = np.random.uniform(1.0, 5.0, (size, size))
    threat_map = np.zeros((size, size))
    threat_centers = [(25, 30, 15), (60, 45, 18), (40, 75, 12), (75, 20, 14)]
    for cx, cy, r in threat_centers:
        for x in range(max(0, cx-r), min(size, cx+r)):
            for y in range(max(0, cy-r), min(size, cy+r)):
                if math.sqrt((x-cx)**2 + (y-cy)**2) <= r:
                    threat_map[x, y] += (r - math.sqrt((x-cx)**2 + (y-cy)**2)) * 15.0 
    return terrain + threat_map


if __name__ == "__main__":
    # Setup configuration
    grid_size = 100
    start_pos = (5, 5)
    goal_pos = (90, 95)
    allocated_fuel = 1500.0
    
    # --- CHANGE THIS THRESHOLD VARIABLE FOR YOUR RESEARCH ---
    max_allowable_threat = 120.0 
    
    cost_map = generate_battlefield(size=grid_size)
    planner = BattlefieldPathPlanner(cost_map, fuel_capacity=allocated_fuel, threat_threshold=max_allowable_threat)
    
    # Run algorithms
    theta_results = planner.solve(start_pos, goal_pos, use_theta_star=True)
    a_star_results = planner.solve(start_pos, goal_pos, use_theta_star=False)
    
    # =================================================================
    # EXTRACTED VARIABLES (AS REQUESTED)
    # =================================================================
    mission_success = theta_results["success"]       
    total_cells_covered = theta_results["cells_covered"] 
    total_fuel_consumed = theta_results["fuel_consumed"] 
    
    # Output display
    print("\n" + "="*40)
    print("      EXTRACTED MISSION METRICS  ")
    print("="*40)
    print(f"Mission Success:    {mission_success}")
    print(f"Total Cells Covered: {total_cells_covered}")
    print(f"Total Fuel Consumed: {total_fuel_consumed:.2f} units")
    print("="*40 + "\n")