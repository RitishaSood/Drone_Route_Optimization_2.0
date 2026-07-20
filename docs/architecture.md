# Architecture Overview

This repo is organized around a single simulation pipeline with three main surfaces:

- Frontend: `frontend/`
- API/backend: `backend/`
- Simulation pipeline: `pipeline/`

## High-Level Flow

1. The frontend collects scenario inputs.
2. The backend validates requests, stores runs, and serves artifacts.
3. The pipeline generates terrain, sensors, final cost grids, and path-planning outputs.
4. The frontend reads artifacts, metrics, and plots from the backend.

## Main Modules

- `backend/src/`
  - run creation and artifact serving
  - swarm simulation bridge
  - security middleware and request validation
- `pipeline/env_generator/`
  - terrain generation
  - sensor/NFZ/environment CSV generation
  - plots for generated inputs
- `pipeline/path_planner/`
  - 2.5D path planning over `final_cost.csv`
  - Lazy 3D A* for 3D mode
  - algorithm metrics and route plots
- `pipeline/swarm_simulation/`
  - Monte Carlo swarm study
  - strategy comparisons
  - summary/trial exports and charts

## Data Flow

```mermaid
flowchart LR
  A[Frontend inputs] --> B[Backend API]
  B --> C[Run folder]
  C --> D[Pipeline outputs]
  D --> E[Artifacts endpoint]
  E --> F[Results and Swarm Study UI]
```

## Key Runtime Outputs

- `data/csv/`
- `data/outputs/`
- `data/plots/`
- `runs/<runId>/config/`
- `runs/<runId>/logs/`

