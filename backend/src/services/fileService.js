const fs = require("fs/promises");
const mime = require("mime-types");

const { getRunPaths, resolveSafeRunFile } = require("../utils/paths");
const { validateCsvFilename, validatePlotFilename } = require("../validators/run.validator");

async function createRunDirectories(paths) {
  await Promise.all([
    fs.mkdir(paths.runDir, { recursive: true }),
    fs.mkdir(paths.configDir, { recursive: true }),
    fs.mkdir(paths.dataDir, { recursive: true }),
    fs.mkdir(paths.csvDir, { recursive: true }),
    fs.mkdir(paths.outputsDir, { recursive: true }),
    fs.mkdir(paths.plotsDir, { recursive: true }),
    fs.mkdir(paths.logsDir, { recursive: true })
  ]);
}

async function readPipelineLog(runId) {
  const paths = getRunPaths(runId);
  const logFile = resolveSafeRunFile(paths.logsDir, "pipeline.log");

  try {
    return await fs.readFile(logFile, "utf8");
  } catch (error) {
    if (error.code === "ENOENT") {
      return "";
    }

    throw error;
  }
}

async function readAlgorithmMetrics(runId) {
  const paths = getRunPaths(runId);
  const filePath = resolveSafeRunFile(paths.outputsDir, "algorithm_metrics.json");

  try {
    const text = await fs.readFile(filePath, "utf8");
    const parsed = JSON.parse(text);
    if (Array.isArray(parsed)) {
      return parsed;
    }
    if (parsed && Array.isArray(parsed.metrics)) {
      return parsed.metrics;
    }
    return [];
  } catch (error) {
    if (error.code === "ENOENT") {
      return [];
    }

    throw error;
  }
}

async function sendPlot(res, runId, filename) {
  validatePlotFilename(filename);

  const paths = getRunPaths(runId);
  const filePath = resolveSafeRunFile(paths.plotsDir, filename);

  await assertFileExists(filePath);
  res.type(mime.lookup(filename) || "image/png");
  res.setHeader("X-Content-Type-Options", "nosniff");
  res.sendFile(filePath);
}

async function sendCsvFile(res, runId, filename) {
  validateCsvFilename(filename);

  const paths = getRunPaths(runId);
  const dataFile = resolveSafeRunFile(paths.csvDir, filename);
  const outputFile = resolveSafeRunFile(paths.outputsDir, filename);

  if (await exists(dataFile)) {
    sendDownload(res, dataFile, filename);
    return;
  }

  if (await exists(outputFile)) {
    sendDownload(res, outputFile, filename);
    return;
  }

  const error = new Error("File not found");
  error.statusCode = 404;
  throw error;
}

async function assertFileExists(filePath) {
  if (!(await exists(filePath))) {
    const error = new Error("File not found");
    error.statusCode = 404;
    throw error;
  }
}

function sendDownload(res, filePath, filename) {
  res.type(mime.lookup(filename) || "text/csv");
  res.setHeader("Content-Disposition", `attachment; filename="${filename}"`);
  res.setHeader("X-Content-Type-Options", "nosniff");
  res.sendFile(filePath);
}

async function exists(filePath) {
  try {
    await fs.access(filePath);
    return true;
  } catch (error) {
    if (error.code === "ENOENT") {
      return false;
    }

    throw error;
  }
}

module.exports = {
  createRunDirectories,
  readPipelineLog,
  readAlgorithmMetrics,
  sendPlot,
  sendCsvFile
};
