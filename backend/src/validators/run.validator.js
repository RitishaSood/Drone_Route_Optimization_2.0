const Joi = require("joi");

const {
  allowedAlgorithms,
  allowedDroneNames,
  allowedPlacementModes,
  allowedThreatTypes
} = require("../config/allowedValues");

const clientIdPattern = /^[A-Za-z0-9_-]+$/;
const runIdPattern = /^[A-Za-z0-9_-]+$/;

const runConfigSchema = Joi.object({
  flightZ: Joi.number().integer().min(0).max(100).required(),
  sensorCount: Joi.number().integer().min(0).max(1000).required(),
  threatTypes: Joi.array()
    .items(Joi.string().valid(...allowedThreatTypes))
    .min(1)
    .unique()
    .required(),
  terrainSeed: Joi.number().integer().min(0).max(2147483647).required(),
  nfzCount: Joi.number().integer().min(0).max(100).required(),
  droneName: Joi.string().valid(...allowedDroneNames).required(),
  placementMode: Joi.string().valid(...allowedPlacementModes).required(),
  algorithm: Joi.string().valid(...allowedAlgorithms).default("cost-field-only")
})
  .required()
  .unknown(true);

const createRunSchema = Joi.object({
  clientId: Joi.string().trim().pattern(clientIdPattern).max(100).required(),
  config: runConfigSchema
})
  .required()
  .unknown(false);

const runIdSchema = Joi.string().trim().pattern(runIdPattern).max(100).required();

const plotFilenameSchema = Joi.string()
  .valid(
    "terrain.png",
    "terrain_3d.png",
    "sensors.png",
    "suitability.png",
    "layers.png",
    "final_cost_heatmap.png",
    "final_cost_binary.png",
    "dijkstra_path.png",
    "astar_path.png",
    "genetic_path.png",
    "monte_carlo_rl_path.png",
    "theta_star_path.png",
    "dstar_lite_path.png",
    "ant_colony_path.png",
    "algorithm_comparison.png"
  )
  .required();

const csvFilenameSchema = Joi.string()
  .valid(
    "terrain_height.csv",
    "terrain_type.csv",
    "sensor.csv",
    "nfz.csv",
    "env.csv",
    "final_cost.csv",
    "algorithm_metrics.csv",
    "dijkstra_path.csv",
    "astar_path.csv",
    "genetic_path.csv",
    "monte_carlo_rl_path.csv",
    "theta_star_path.csv",
    "dstar_lite_path.csv",
    "ant_colony_path.csv"
  )
  .required();

function validateCreateRunBody(body) {
  return validateSchema(createRunSchema, body, "Invalid run request");
}

function validateRunConfig(config) {
  return validateSchema(runConfigSchema, config, "Invalid run config");
}

function validateRunId(runId) {
  return validateSchema(runIdSchema, runId, "Invalid runId");
}

function validatePlotFilename(filename) {
  return validateSchema(plotFilenameSchema, filename, "Invalid plot filename");
}

function validateCsvFilename(filename) {
  return validateSchema(csvFilenameSchema, filename, "Invalid file filename");
}

function validateClientId(clientId) {
  return validateSchema(
    Joi.string().trim().pattern(clientIdPattern).max(100).required(),
    clientId,
    "Invalid clientId"
  );
}

function validateSchema(schema, value, message) {
  const { value: validated, error } = schema.validate(value, {
    abortEarly: false,
    convert: true,
    stripUnknown: false
  });

  if (error) {
    const validationError = new Error(message);
    validationError.statusCode = 400;
    validationError.details = error.details.map((detail) => detail.message);
    throw validationError;
  }

  return validated;
}

module.exports = {
  validateClientId,
  validateCreateRunBody,
  validateCsvFilename,
  validateRunConfig,
  validatePlotFilename,
  validateRunId
};
