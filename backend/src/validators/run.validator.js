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
  planningMode: Joi.string().valid("2.5D", "3D").default("2.5D"),
  flightZ: Joi.number().integer().min(0).max(100).required(),
  route: Joi.object({
    start: Joi.object({
      x: Joi.number().integer().min(0).max(99).required(),
      y: Joi.number().integer().min(0).max(99).required(),
      z: Joi.number().integer().min(0).max(100).required()
    }).required(),
    end: Joi.object({
      x: Joi.number().integer().min(0).max(99).required(),
      y: Joi.number().integer().min(0).max(99).required(),
      z: Joi.number().integer().min(0).max(100).required()
    }).required()
  }).required(),
  terrainSeed: Joi.number().integer().min(0).max(2147483647).required(),
  threatTypes: Joi.array()
    .items(Joi.string().valid(...allowedThreatTypes))
    .min(1)
    .unique()
    .required(),
  sensorCount: Joi.number().integer().min(0).max(1000).required(),
  sensorMode: Joi.string().valid("auto", "manual-counts", "manual-table", "uploaded", "pasted").default("auto"),
  sensorCounts: Joi.object({
    radar: Joi.number().integer().min(0).required(),
    ir: Joi.number().integer().min(0).required(),
    acoustic: Joi.number().integer().min(0).required(),
    visual: Joi.number().integer().min(0).required()
  }).default(),
  manualSensors: Joi.array().items(Joi.object()).default([]),
  inputMode: Joi.string().valid("generated", "uploaded", "pasted", "hybrid").default("generated"),
  inputSources: Joi.object({
    terrain_height: Joi.string().valid("generated", "uploaded", "pasted").required(),
    terrain_type: Joi.string().valid("generated", "uploaded", "pasted").required(),
    sensor: Joi.string().valid("generated", "manual-table", "uploaded", "pasted").required(),
    nfz: Joi.string().valid("generated", "uploaded", "pasted").required(),
    env: Joi.string().valid("generated", "uploaded", "pasted").required()
  }).default(),
  nfzCount: Joi.number().integer().min(0).max(100).required(),
  droneName: Joi.string().valid(...allowedDroneNames).required(),
  placementMode: Joi.string().valid(...allowedPlacementModes).required(),
  algorithmMode: Joi.string().valid("run-all").default("run-all"),
  algorithms: Joi.array().items(Joi.string().valid(...allowedAlgorithms)).default([]),
  algorithm: Joi.string().valid(...allowedAlgorithms).default("cost-field-only"),
  environmentEnabled: Joi.boolean().default(false),
  environment: Joi.object({
    windEnabled: Joi.boolean().default(false),
    windSpeed: Joi.number().required(),
    windDirection: Joi.number().required(),
    gustSpeed: Joi.number().required(),
    rainEnabled: Joi.boolean().default(false),
    rainIntensity: Joi.number().required(),
    fogEnabled: Joi.boolean().default(false),
    fogIntensity: Joi.number().required(),
    snowEnabled: Joi.boolean().default(false),
    snowIntensity: Joi.number().required(),
    hailEnabled: Joi.boolean().default(false),
    hailIntensity: Joi.number().required(),
    turbulenceEnabled: Joi.boolean().default(false),
    turbulenceIntensity: Joi.number().required(),
    temperatureEnabled: Joi.boolean().default(false),
    temperatureC: Joi.number().required(),
    thunderstormEnabled: Joi.boolean().default(false),
    thunderstorm: Joi.boolean().default(false)
  }).default(),
  timeAware: Joi.boolean().default(false),
  missionDeadlineMinutes: Joi.number().min(0).default(120),
  timeStepSeconds: Joi.number().min(1).default(60),
  timeOfDayEnabled: Joi.boolean().default(false),
  missionStartHour: Joi.number().min(0).max(23).default(6),
  missionDurationHours: Joi.number().min(0).default(6),
  timeSampleIntervalMinutes: Joi.number().min(1).default(30),
  ewJammingEnabled: Joi.boolean().default(false),
  advancedThreatFalloffEnabled: Joi.boolean().default(false),
  falloffConfig: Joi.object().default({}),
  coverageConfig: Joi.object().default({}),
  zMin: Joi.number().integer().min(0).max(100).optional(),
  zMax: Joi.number().integer().min(0).max(100).optional(),
  preferredZ: Joi.number().integer().min(0).max(100).optional(),
  altitudePenaltyWeight: Joi.number().min(0).optional(),
  useLazy3D: Joi.boolean().default(false)
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
    "lazy_3d_route.png",
    "lazy_3d_route_over_terrain.png",
    "lazy_3d_altitude_profile.png",
    "lazy_3d_cost_profile.png",
    "lazy_3d_stats_summary.png",
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
