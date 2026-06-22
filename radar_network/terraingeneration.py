import numpy as np
import matplotlib.pyplot as plt
from matplotlib.colors import ListedColormap, BoundaryNorm
from mpl_toolkits.mplot3d import Axes3D
import noise
import random

class TerrainGenerator:
    """
    Generates a realistic 2D/3D battlefield terrain grid using Fractal Brownian Motion (fBm),
    Gaussian structural features, and slope/cost assessment matrices tailored for 
    UAV routing algorithms and Monte Carlo simulations.
    """
    def __init__(self, grid_size=100, scale=40.0, octaves=6, persistence=0.5, lacunarity=2.0, seed=42):
        self.grid_size = grid_size
        self.scale = scale
        self.octaves = octaves
        self.persistence = persistence
        self.lacunarity = lacunarity
        self.seed = seed
        
        # Matrix Initializations
        self.terrain = np.zeros((grid_size, grid_size))
        self.terrain_type = np.empty((grid_size, grid_size), dtype=object)
        self.slope_map = np.zeros((grid_size, grid_size))
        self.cost_map = np.zeros((grid_size, grid_size))
        self.high_ground_positions = []

        # Define Classifications and Colors
        self.classes = ['Valley', 'Plain', 'Hill', 'Highland', 'Mountain']
        self.bounds = [0, 150, 350, 600, 800, 1000]
        self.cmap_colors = ['#2B4C7E', '#4A7C59', '#8C9A6B', '#A07855', '#D4A373'] # Tactical palette

    def generate_base_terrain(self):
        print("ENTER generate_base_terrain")

        base = np.zeros((self.grid_size, self.grid_size))

        for i in range(self.grid_size):
            print("ROW", i)

        for j in range(self.grid_size):
            val = noise.pnoise2(
                i / self.scale,
                j / self.scale,
                octaves=self.octaves,
                persistence=self.persistence,
                lacunarity=self.lacunarity,
                repeatx=self.grid_size,
                repeaty=self.grid_size,
                base=self.seed
            )

            base[i, j] = val

        print("EXIT generate_base_terrain")

        min_val, max_val = base.min(), base.max()

        if max_val != min_val:
           self.terrain = 1000.0 * (base - min_val) / (max_val - min_val)
        else:
            self.terrain = np.zeros((self.grid_size, self.grid_size))

        return self.terrain

    def _apply_gaussian_influence(self, center_x, center_y, radius, profile_magnitude):
        """Helper to safely construct an isolated normalized Gaussian distribution kernel over the grid."""
        x = np.arange(0, self.grid_size)
        y = np.arange(0, self.grid_size)
        xx, yy = np.meshgrid(x, y)
        
        # Calculate squared Euclidean distances
        distance_sq = (xx - center_x)**2 + (yy - center_y)**2
        # Formulate spatial Gaussian weight
        kernel = np.exp(-distance_sq / (2.0 * (radius ** 2)))
        return kernel * profile_magnitude

    def add_ridges(self, num_ridges=3, ridge_height=150, ridge_width=8.0):
        """Adds strategic Gaussian mountain ridges across unique spatial locations."""
        for _ in range(num_ridges):
            # Safe padding boundaries from edges
            cx, cy = np.random.randint(20, self.grid_size-20, size=2)
            ridge = self._apply_gaussian_influence(cx, cy, ridge_width, ridge_height)
            self.terrain = np.clip(self.terrain + ridge, 0, 1000)

    def add_valleys(self, num_valleys=2, valley_depth=120, valley_width=12.0):
        """Carves out localized river beds/valleys using negative Gaussian kernels."""
        for _ in range(num_valleys):
            cx, cy = np.random.randint(15, self.grid_size-15, size=2)
            valley = self._apply_gaussian_influence(cx, cy, valley_width, valley_depth)
            self.terrain = np.clip(self.terrain - valley, 0, 1000)

    def classify_terrain(self):
        """Classifies each coordinate box based on absolute elevation boundaries."""
        indices = np.digitize(self.terrain, self.bounds) - 1
        indices = np.clip(indices, 0, len(self.classes) - 1)
        
        class_mapping = np.array(self.classes)
        self.terrain_type = class_mapping[indices]
        
        # Identify Strategic High Grounds (Local Maxima inside Mountain regions)
        self.high_ground_positions = []
        for i in range(2, self.grid_size - 2):
            for j in range(2, self.grid_size - 2):
                if self.terrain[i, j] >= 850:  
                    neighborhood = self.terrain[i-2:i+3, j-2:j+3]
                    if self.terrain[i, j] == np.max(neighborhood):
                        if (i, j) not in self.high_ground_positions:
                            self.high_ground_positions.append((i, j))
                            if len(self.high_ground_positions) >= 5: 
                                break
            if len(self.high_ground_positions) >= 5:
                break
                
        return self.terrain_type

    def calculate_slope(self):
        """Computes structural slope gradients using spatial central differences."""
        dy, dx = np.gradient(self.terrain)
        self.slope_map = np.sqrt(dx**2 + dy**2)
        return self.slope_map

    def generate_cost_map(self, elevation_weight=0.005, slope_weight=2.5):
        """Builds static navigation cost map matching kinematic routing requirements."""
        self.cost_map = 1.0 + (self.terrain * elevation_weight) + (self.slope_map * slope_weight)
        return self.cost_map

    def get_elevation(self, x, y):
        """Accessor providing absolute point boundary elevation calculations safely."""
        if 0 <= x < self.grid_size and 0 <= y < self.grid_size:
            return self.terrain[int(x), int(y)]
        return None

    def sample_random_points(self, n=10):
        """Provides random uniform point pairs natively used for Monte Carlo simulation drops."""
        coords = np.random.randint(0, self.grid_size, size=(n, 2))
        return [tuple(pt) for pt in coords]

    def plot_2d(self):
        """Renders tactical 2D discrete Categorized Layout & Strategic Assets Map."""
        plt.figure("2D Tactical Terrain", figsize=(9, 7))
        custom_cmap = ListedColormap(self.cmap_colors)
        norm = BoundaryNorm(self.bounds, custom_cmap.N)
        
        img = plt.imshow(self.terrain, cmap=custom_cmap, norm=norm, origin='lower')
        cbar = plt.colorbar(img, ticks=[75, 250, 475, 700, 900])
        cbar.ax.set_yticklabels(self.classes)
        cbar.set_label('Tactical Terrain Classification Level')
        
        if self.high_ground_positions:
            hx, hy = zip(*self.high_ground_positions)
            plt.scatter(hy, hx, color='red', marker='^', s=100, edgecolor='black', label='Observation Outpost')
            plt.legend(loc='upper right')

        plt.title("2D Strategic Battlefield Terrain Classification Map")
        plt.xlabel("Grid X-Coordinate")
        plt.ylabel("Grid Y-Coordinate")
        plt.grid(True, alpha=0.3, linestyle='--')
        # block=False prevents VS Code from hanging here
        plt.show(block=False)

    def plot_3d(self):
        """Displays full interactive 3D Topographical Mesh surface."""
        fig = plt.figure("3D Surface Map", figsize=(11, 8))
        ax = fig.add_subplot(111, projection='3d')
        
        x = np.arange(0, self.grid_size)
        y = np.arange(0, self.grid_size)
        xx, yy = np.meshgrid(x, y)
        
        surf = ax.plot_surface(xx, yy, self.terrain, cmap='terrain', edgecolor='none', alpha=0.9, linewidth=0)
        fig.colorbar(surf, ax=ax, shrink=0.5, aspect=10, label='Elevation (Meters)')
        
        ax.set_title("3D Continuous Surface Topographical Visualization")
        ax.set_xlabel("Grid X")
        ax.set_ylabel("Grid Y")
        ax.set_zlabel("Elevation (m)")
        ax.set_zlim(0, 1000)
        ax.view_init(elev=38, azim=-125)
        
        # Keeps windows open safely at the very end of processing scripts
        plt.show()

if __name__ == "__main__":
    print("[INFO] Initializing Terrain Generation Pipeline for Drone Research...")
    
    # 1. Establish structural runtime state seeds
    random_seed = random.randint(0, 999999)
    np.random.seed(random_seed)  # Syncs NumPy state to the randomized seed
    print(f"[SEED] Active Run Target Configuration Seed: {random_seed}")
    
    tg = TerrainGenerator(grid_size=100, scale=40.0, octaves=6, persistence=0.5, lacunarity=2.0, seed=random_seed)
    
    # 2. Base Matrix Generation
    tg.generate_base_terrain()
    
    # 3. Add Geomorphological Structures
    tg.add_ridges(num_ridges=4, ridge_height=180, ridge_width=6.0)
    tg.add_valleys(num_valleys=2, valley_depth=150, valley_width=10.0)
    
    # 4. Process Data Layers
    tg.classify_terrain()
    tg.calculate_slope()
    cost_map = tg.generate_cost_map()

    # 5. Output Summary of Terrain Data
    height_matrix = tg.terrain
    print(f"[DATA] Height Matrix Shape: {height_matrix.shape}")
    print(height_matrix)
    
    print(f"[SUCCESS] Terrain processing complete.")
    print(f" -> Minimum Elevation Found   : {tg.terrain.min():.2f} m")
    print(f" -> Maximum Elevation Found   : {tg.terrain.max():.2f} m")
    print(f" -> Strategic Outposts Identified: {tg.high_ground_positions}")
    
    # 5. Sample Random Coordinates
    mc_drop_points = tg.sample_random_points(n=5)
    print(f" -> Sampled Monte Carlo Drop Targets: {mc_drop_points}")
    
    # 6. Open both windows simultaneously inside VS Code
    tg.plot_2d()
    tg.plot_3d()