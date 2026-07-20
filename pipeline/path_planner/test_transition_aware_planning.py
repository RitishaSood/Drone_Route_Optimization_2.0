from __future__ import annotations

import json

import numpy as np

from pipeline.path_planner.algorithms.Astar import run_astar
from pipeline.path_planner.algorithms.dijkstra import run_dijkstra
from pipeline.path_planner.vehicle_model import TransitionCostAdapter, TransitionWeights


def main() -> int:
    grid = np.array(
        [
            [1.0, 2.0, 3.0],
            [1.0, 50.0, 1.0],
            [1.0, 1.0, 1.0],
        ],
        dtype=float,
    )
    adapter = TransitionCostAdapter(grid, "IAI Heron", None, TransitionWeights(), 1.0, 0.1)

    astar_plain = run_astar(grid, (0, 0), (2, 2), 50)
    astar_transition = run_astar(grid, (0, 0), (2, 2), 50, transition_cost_adapter=adapter)
    dijkstra_plain = run_dijkstra(grid, (0, 0), (2, 2), 50)
    dijkstra_transition = run_dijkstra(grid, (0, 0), (2, 2), 50, transition_cost_adapter=adapter)

    for result in (astar_plain, astar_transition, dijkstra_plain, dijkstra_transition):
        if result["success"]:
            assert result["path"]

    assert astar_plain.get("transitionAware", False) is False
    assert astar_transition.get("transitionAware", False) is True
    assert dijkstra_plain.get("transitionAware", False) is False
    assert dijkstra_transition.get("transitionAware", False) is True

    print(json.dumps({
        "astar_plain": astar_plain["totalCost"],
        "astar_transition": astar_transition["totalCost"],
        "dijkstra_plain": dijkstra_plain["totalCost"],
        "dijkstra_transition": dijkstra_transition["totalCost"],
    }, indent=2))

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
