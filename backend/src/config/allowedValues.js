const allowedThreatTypes = ["radar", "ir", "acoustic", "visual"];

const allowedPlacementModes = ["greedy", "random", "strategic"];

const allowedDroneNames = [
  "IAI Heron",
  "Heron TP",
  "Rustom-2 (TAPAS BH-201)",
  "MQ-9 Reaper",
  "Switch UAV",
  "DRDO Ghatak",
  "Netra UAV",
  "Harpy",
  "Searcher",
  "Black Hornet",
  "Nagastra-1"
];

const allowedAlgorithms = [
  "cost-field-only",
  "dijkstra",
  "astar",
  "theta-star",
  "dstar-lite",
  "ant-colony",
  "genetic",
  "monte-carlo-rl"
];

module.exports = {
  allowedAlgorithms,
  allowedDroneNames,
  allowedPlacementModes,
  allowedThreatTypes
};
