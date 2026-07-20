const fs = require("fs/promises");

const { allowedAlgorithms } = require("../config/allowedValues");
const { validateRunConfig } = require("../validators/run.validator");

const DEFAULTS = {
  gridSize: 100,
  cellScaleM: 1000,
  zScaleM: 100,
  algorithm: "cost-field-only"
};

const AUTO_COVERAGE_TARGET = 0.92;
const AUTO_COVERAGE_MIN = 0.9;
const AUTO_COVERAGE_MAX = 0.95;

function validateScenarioConfig(config) {
  const validated = validateRunConfig(config);
  const normalizedCoverageConfig = normalizeCoverageConfig(validated.coverageConfig || {});
  const sensorCount = deriveAutoSensorCount(validated.sensorCount, validated.sensorMode, normalizedCoverageConfig);

  return {
    ...validated,
    algorithm: validated.algorithm || DEFAULTS.algorithm,
    sensorCount,
    coverageConfig: normalizedCoverageConfig
  };
}

function normalizeCoveragePercent(value) {
  if (typeof value !== "number" || !Number.isFinite(value) || value <= 0) {
    return AUTO_COVERAGE_TARGET;
  }

  const pct = value > 1 ? value / 100 : value;
  return Math.min(AUTO_COVERAGE_MAX, Math.max(AUTO_COVERAGE_MIN, pct));
}

function normalizeCoverageConfig(coverageConfig) {
  const normalized = { ...(coverageConfig || {}) };
  const target = normalizeCoveragePercent(
    normalized.targetCoveragePercent ?? normalized.coverageThreshold
  );

  normalized.coverageTargetEnabled = normalized.coverageTargetEnabled !== false;
  normalized.targetCoveragePercent = target;
  normalized.coverageThreshold = target;

  if (typeof normalized.minimumSensorSpacing !== "number" || !Number.isFinite(normalized.minimumSensorSpacing)) {
    normalized.minimumSensorSpacing = 10;
  }
  if (typeof normalized.maxSensors !== "number" || !Number.isFinite(normalized.maxSensors)) {
    normalized.maxSensors = 64;
  }
  if (normalized.maxSensors < 1) {
    normalized.maxSensors = 1;
  }
  normalized.useQuadrantDistribution = normalized.useQuadrantDistribution !== false;

  return normalized;
}

function deriveAutoSensorCount(sensorCount, sensorMode, coverageConfig) {
  if (sensorMode !== "auto" || !coverageConfig.coverageTargetEnabled) {
    return sensorCount;
  }

  const target = normalizeCoveragePercent(coverageConfig.targetCoveragePercent);
  const maxSensors = Math.max(1, Math.min(1000, Math.floor(coverageConfig.maxSensors || 64)));
  const baseCount = Math.max(1, Math.min(1000, Math.floor(sensorCount || 0)));

  // Move auto placement toward a high-coverage operating point without changing
  // the manual sensor workflows. The target is intentionally biased into the
  // 90-95% band so the default auto mode produces denser layouts.
  const densityBoost = 1 + target * 0.85;
  const targetCount = Math.ceil(baseCount * densityBoost);

  return Math.min(maxSensors, Math.max(baseCount, targetCount));
}

async function writeScenarioEnv(filename, config) {
  const algorithm = normalizeAlgorithm(config.algorithm);
  const env = config.environment || {};
  const inputSources = config.inputSources || {};
  const csvInputs = config.csvInputs || {};
  const route = config.route || {};
  const start = route.start || {};
  const end = route.end || {};

  const lines = [
    `GRID_SIZE=${DEFAULTS.gridSize}`,
    `CELL_SCALE_M=${DEFAULTS.cellScaleM}`,
    `Z_SCALE_M=${DEFAULTS.zScaleM}`,
    `PLANNING_MODE=${config.planningMode || "2.5D"}`,
    `FLIGHT_Z=${config.flightZ}`,
    `START_X=${start.x ?? 0}`,
    `START_Y=${start.y ?? 0}`,
    `START_Z=${start.z ?? config.flightZ}`,
    `END_X=${end.x ?? 99}`,
    `END_Y=${end.y ?? 99}`,
    `END_Z=${end.z ?? config.flightZ}`,
    `SENSOR_COUNT=${config.sensorCount}`,
    `SENSOR_MODE=${config.sensorMode || "auto"}`,
    `SENSOR_COUNTS=${JSON.stringify(config.sensorCounts || {})}`,
    `MANUAL_SENSORS=${JSON.stringify(config.manualSensors || [])}`,
    `INPUT_MODE=${config.inputMode || "generated"}`,
    `INPUT_SOURCES=${JSON.stringify(inputSources)}`,
    `CSV_INPUTS=${JSON.stringify(csvInputs)}`,
    `THREAT_TYPES=${config.threatTypes.join(",")}`,
    `TERRAIN_SEED=${config.terrainSeed}`,
    `NFZ_COUNT=${config.nfzCount}`,
    `DRONE_NAME=${config.droneName}`,
    `PLACEMENT_MODE=${config.placementMode}`,
    `ALGORITHM_MODE=${config.algorithmMode || "run-all"}`,
    `ALGORITHMS=${Array.isArray(config.algorithms) ? config.algorithms.join(",") : ""}`,
    `ALGORITHM=${algorithm}`,
    `ENVIRONMENT_ENABLED=${Boolean(config.environmentEnabled)}`,
    `WIND_ENABLED=${Boolean(env.windEnabled)}`,
    `WIND_SPEED=${env.windSpeed ?? 0}`,
    `WIND_DIRECTION=${env.windDirection ?? 0}`,
    `GUST_SPEED=${env.gustSpeed ?? 0}`,
    `RAIN_ENABLED=${Boolean(env.rainEnabled)}`,
    `RAIN_INTENSITY=${env.rainIntensity ?? 0}`,
    `FOG_ENABLED=${Boolean(env.fogEnabled)}`,
    `FOG_INTENSITY=${env.fogIntensity ?? 0}`,
    `SNOW_ENABLED=${Boolean(env.snowEnabled)}`,
    `SNOW_INTENSITY=${env.snowIntensity ?? 0}`,
    `HAIL_ENABLED=${Boolean(env.hailEnabled)}`,
    `HAIL_INTENSITY=${env.hailIntensity ?? 0}`,
    `TURBULENCE_ENABLED=${Boolean(env.turbulenceEnabled)}`,
    `TURBULENCE_INTENSITY=${env.turbulenceIntensity ?? 0}`,
    `TEMPERATURE_ENABLED=${Boolean(env.temperatureEnabled)}`,
    `TEMPERATURE_C=${env.temperatureC ?? 20}`,
    `THUNDERSTORM_ENABLED=${Boolean(env.thunderstormEnabled)}`,
    `THUNDERSTORM=${Boolean(env.thunderstorm)}`,
    `TIME_AWARE=${Boolean(config.timeAware)}`,
    `MISSION_DEADLINE_MINUTES=${config.missionDeadlineMinutes ?? 120}`,
    `TIME_STEP_SECONDS=${config.timeStepSeconds ?? 60}`,
    `TIME_OF_DAY_ENABLED=${Boolean(config.timeOfDayEnabled)}`,
    `MISSION_START_HOUR=${config.missionStartHour ?? 6}`,
    `MISSION_DURATION_HOURS=${config.missionDurationHours ?? 6}`,
    `TIME_SAMPLE_INTERVAL_MINUTES=${config.timeSampleIntervalMinutes ?? 30}`,
    `EW_JAMMING_ENABLED=${Boolean(config.ewJammingEnabled)}`,
    `ADVANCED_THREAT_FALLOFF_ENABLED=${Boolean(config.advancedThreatFalloffEnabled)}`,
    `FALLOFF_CONFIG=${JSON.stringify(config.falloffConfig || {})}`,
    `COVERAGE_CONFIG=${JSON.stringify(config.coverageConfig || {})}`,
    `Z_MIN=${config.zMin ?? ""}`,
    `Z_MAX=${config.zMax ?? ""}`,
    `PREFERRED_Z=${config.preferredZ ?? ""}`,
    `ALTITUDE_PENALTY_WEIGHT=${config.altitudePenaltyWeight ?? ""}`,
    `USE_LAZY_3D=${Boolean(config.useLazy3D)}`
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
