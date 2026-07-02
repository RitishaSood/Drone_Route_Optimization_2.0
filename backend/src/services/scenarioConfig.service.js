const fs = require("fs/promises");

const { allowedAlgorithms } = require("../config/allowedValues");
const { validateRunConfig } = require("../validators/run.validator");

const DEFAULTS = {
  gridSize: 100,
  cellScaleM: 1000,
  zScaleM: 100,
  algorithm: "cost-field-only"
};

function validateScenarioConfig(config) {
  const validated = validateRunConfig(config);

  return {
    flightZ: validated.flightZ,
    sensorCount: validated.sensorCount,
    threatTypes: validated.threatTypes,
    terrainSeed: validated.terrainSeed,
    nfzCount: validated.nfzCount,
    droneName: validated.droneName,
    placementMode: validated.placementMode,
    algorithm: validated.algorithm || DEFAULTS.algorithm
  };
}

async function writeScenarioEnv(filename, config) {
  const algorithm = normalizeAlgorithm(config.algorithm);

  const lines = [
    `GRID_SIZE=${DEFAULTS.gridSize}`,
    `CELL_SCALE_M=${DEFAULTS.cellScaleM}`,
    `Z_SCALE_M=${DEFAULTS.zScaleM}`,
    `FLIGHT_Z=${config.flightZ}`,
    `SENSOR_COUNT=${config.sensorCount}`,
    `THREAT_TYPES=${config.threatTypes.join(",")}`,
    `TERRAIN_SEED=${config.terrainSeed}`,
    `NFZ_COUNT=${config.nfzCount}`,
    `DRONE_NAME=${config.droneName}`,
    `PLACEMENT_MODE=${config.placementMode}`,
    `ALGORITHM=${algorithm}`
  ];

  await fs.writeFile(filename, `${lines.join("\n")}\n`, "utf8");
}

function normalizeAlgorithm(algorithm) {
  const candidate = typeof algorithm === "string" && algorithm.trim()
    ? algorithm.trim().toLowerCase()
    : DEFAULTS.algorithm;

  if (!allowedAlgorithms.includes(candidate)) {
    const error = new Error("Unsupported algorithm");
    error.statusCode = 400;
    throw error;
  }

  return candidate;
}

module.exports = {
  validateScenarioConfig,
  writeScenarioEnv
};
