const path = require("path");

function getRunsRoot() {
  return path.resolve(process.env.RUNS_DIR || path.join(process.cwd(), "../runs"));
}

function getRunPaths(runId) {
  assertRunId(runId);

  const runDir = path.join(getRunsRoot(), runId);
  const configDir = path.join(runDir, "config");
  const dataDir = path.join(runDir, "data");
  const csvDir = path.join(dataDir, "csv");
  const outputsDir = path.join(dataDir, "outputs");
  const plotsDir = path.join(dataDir, "plots");
  const logsDir = path.join(runDir, "logs");

  return {
    runDir,
    configDir,
    dataDir,
    csvDir,
    outputsDir,
    plotsDir,
    logsDir,
    scenarioConfigFile: path.join(configDir, "scenario.env"),
    pipelineLogFile: path.join(logsDir, "pipeline.log")
  };
}

function resolveSafeRunFile(directory, filename) {
  assertSafeFilename(filename);

  const resolvedDirectory = path.resolve(directory);
  const resolvedFile = path.resolve(resolvedDirectory, filename);

  if (!resolvedFile.startsWith(`${resolvedDirectory}${path.sep}`)) {
    const error = new Error("Invalid filename");
    error.statusCode = 400;
    throw error;
  }

  return resolvedFile;
}

function assertRunId(value) {
  if (
    typeof value !== "string" ||
    value.length === 0 ||
    value.length > 100 ||
    !/^[A-Za-z0-9_-]+$/.test(value)
  ) {
    const error = new Error("Invalid runId");
    error.statusCode = 400;
    throw error;
  }
}

function assertSafeFilename(value) {
  if (
    typeof value !== "string" ||
    value.length === 0 ||
    value.length > 100 ||
    value.includes("..") ||
    value.includes("/") ||
    value.includes("\\") ||
    !/^[A-Za-z0-9._-]+$/.test(value)
  ) {
    const error = new Error("Invalid filename");
    error.statusCode = 400;
    throw error;
  }
}

module.exports = {
  getRunsRoot,
  getRunPaths,
  resolveSafeRunFile
};
