# Swarm Study

The swarm study is a Monte Carlo layer above the existing route planner.

## Purpose

It compares how swarm size and route strategy affect mission success under threat uncertainty.

## Strategies

- `single_route`
- `split_routes`
- `decoy_lead`
- `distributed_routing`

## Sampled Variables

- radar detection scale
- SAM kill probability
- EW effectiveness
- communication loss
- weather severity

## Outputs

- `outputs/swarm_monte_carlo_summary.json`
- `outputs/swarm_monte_carlo_summary.csv`
- `outputs/swarm_monte_carlo_trials.csv`
- `outputs/swarm_config_used.json`
- `outputs/swarm_strategy_routes.json`

## Plots

- `plots/swarm_success_probability.png`
- `plots/swarm_survivors_by_strategy.png`
- `plots/swarm_coverage_by_strategy.png`
- `plots/swarm_cost_by_strategy.png`
- `plots/swarm_success_vs_swarm_size.png`
- `plots/swarm_loss_breakdown.png`

## Backend Routes

- `POST /api/runs/:runId/swarm-simulation`
- `GET /api/runs/:runId/swarm-summary`
- `GET /api/runs/:runId/swarm-trials`

## Notes

- The swarm system is separate from the single-drone planner.
- Swarm outputs are discovered dynamically from the run folder.
- The frontend should treat missing swarm outputs as unavailable, not as an error.

