# Run Flow

This project uses a run folder per simulation execution.

## Standard Run Flow

1. The user configures a scenario in the frontend.
2. The frontend sends the config to the backend.
3. The backend creates a run folder and stores the validated config.
4. The pipeline generates CSV inputs and derived outputs.
5. The backend serves metrics and artifacts from the run folder.
6. The frontend renders tables, downloads, and plots from those artifacts.

## 2.5D Mode

- Uses fixed-altitude route planning.
- Start and goal Z are derived from the selected flight altitude.
- Route planners consume `final_cost.csv`.

## 3D Mode

- Uses Lazy 3D A* only.
- Start and goal Z can be edited directly.
- The route plot and altitude profile are shown from 3D outputs.

## Important Files

- `final_cost.csv`
- `algorithm_metrics.json`
- `algorithm_metrics.csv`
- `terrain_height.csv`
- `terrain_type.csv`
- `sensor.csv`
- `nfz.csv`
- `env.csv`

## Common Artifacts

- Terrain plots
- Sensor and suitability plots
- Final cost plots
- Algorithm comparison plots
- Pathfinding plots
- Swarm Monte Carlo summary and trials

