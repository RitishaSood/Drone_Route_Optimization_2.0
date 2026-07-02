const Run = require("../models/Run");
const fileService = require("../services/fileService");
const runManager = require("../services/runManager.service");
const {
  validateClientId,
  validateCreateRunBody,
  validateCsvFilename,
  validatePlotFilename,
  validateRunId
} = require("../validators/run.validator");

async function createRun(req, res, next) {
  try {
    const validatedBody = validateCreateRunBody(req.body);
    const result = await runManager.createQueuedRun(validatedBody);

    res.status(201).json({
      runId: result.runId,
      status: result.status
    });
  } catch (error) {
    next(error);
  }
}

async function listRuns(req, res, next) {
  try {
    const query = {};

    if (typeof req.query.clientId === "string" && req.query.clientId.trim()) {
      query.clientId = validateClientId(req.query.clientId);
    }

    const runs = await Run.find(query)
      .sort({ createdAt: -1 })
      .lean();

    res.json({ runs });
  } catch (error) {
    next(error);
  }
}

async function getRun(req, res, next) {
  try {
    validateRunId(req.params.runId);
    const run = await findRunOrThrow(req.params.runId);

    res.json({ run });
  } catch (error) {
    next(error);
  }
}

async function getRunStatus(req, res, next) {
  try {
    validateRunId(req.params.runId);
    const run = await findRunOrThrow(req.params.runId);

    res.json({
      runId: run.runId,
      status: run.status,
      startedAt: run.startedAt,
      finishedAt: run.finishedAt,
      error: run.error
    });
  } catch (error) {
    next(error);
  }
}

async function getRunAlgorithmMetrics(req, res, next) {
  try {
    validateRunId(req.params.runId);
    await findRunOrThrow(req.params.runId);

    const metrics = await fileService.readAlgorithmMetrics(req.params.runId);

    res.json({
      runId: req.params.runId,
      available: Array.isArray(metrics) && metrics.length > 0,
      metrics: metrics || []
    });
  } catch (error) {
    next(error);
  }
}

async function getRunLogs(req, res, next) {
  try {
    validateRunId(req.params.runId);
    await findRunOrThrow(req.params.runId);
    const log = await fileService.readPipelineLog(req.params.runId);

    res.type("text/plain; charset=utf-8").send(log);
  } catch (error) {
    next(error);
  }
}

async function getRunPlot(req, res, next) {
  try {
    validateRunId(req.params.runId);
    validatePlotFilename(req.params.filename);
    await findRunOrThrow(req.params.runId);
    await fileService.sendPlot(res, req.params.runId, req.params.filename);
  } catch (error) {
    next(error);
  }
}

async function getRunFile(req, res, next) {
  try {
    validateRunId(req.params.runId);
    validateCsvFilename(req.params.filename);
    await findRunOrThrow(req.params.runId);
    await fileService.sendCsvFile(res, req.params.runId, req.params.filename);
  } catch (error) {
    next(error);
  }
}

async function findRunOrThrow(runId) {
  const run = await Run.findOne({ runId }).lean();

  if (!run) {
    const error = new Error("Run not found");
    error.statusCode = 404;
    throw error;
  }

  return run;
}

module.exports = {
  createRun,
  listRuns,
  getRun,
  getRunStatus,
  getRunAlgorithmMetrics,
  getRunLogs,
  getRunPlot,
  getRunFile
};
