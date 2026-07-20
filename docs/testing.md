# Testing

This repo uses multiple test layers.

## What To Test

- Python path planner tests
- Python swarm simulation test
- Frontend build and lint
- Backend API routes
- Docker build and compose startup

## Useful Commands

- `python -m pipeline.path_planner.test_vehicle_model`
- `python -m pipeline.path_planner.test_transition_aware_planning`
- `python -m pipeline.path_planner.test_lazy_astar_3d`
- `python -m pipeline.path_planner.test_environment_time_ew_metrics`
- `python -m pipeline.swarm_simulation.test_swarm_simulation`
- `cd frontend && npm run build`
- `cd frontend && npm run lint`
- `docker compose build --no-cache`
- `docker compose up -d`

## What Success Looks Like

- 2.5D runs generate `final_cost.csv` and route artifacts.
- 3D runs use Lazy 3D A* and generate 3D plots.
- Swarm study generates summary CSV/JSON and plot files.
- Backend artifact discovery returns only allowlisted files.
- Frontend results render without null or undefined placeholders.

## Troubleshooting

- If swarm simulation fails with Python import errors, check the container runtime and Python dependencies.
- If the frontend shows `Failed to fetch`, verify backend availability, proxy settings, and HTTPS/CORS rules.
- If 3D results look flat, check that the run used `planningMode=3D` and `useLazy3D=true`.

