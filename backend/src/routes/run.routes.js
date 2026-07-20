const express = require("express");
const rateLimit = require("express-rate-limit");

const runController = require("../controllers/run.controller");
const swarmService = require("../services/swarmService");

const router = express.Router();

const createRunLimiter = rateLimit({
  windowMs: 15 * 60 * 1000,
  max: 10,
  standardHeaders: true,
  legacyHeaders: false,
  handler: (_req, res) => {
    res.status(429).json({
      error: "Run creation rate limit exceeded. Please try again later."
    });
  }
});

router.post("/", createRunLimiter, runController.createRun);
router.get("/", runController.listRuns);
router.get("/:runId", runController.getRun);
router.get("/:runId/status", runController.getRunStatus);
router.get("/:runId/algorithm-metrics", runController.getRunAlgorithmMetrics);
router.get("/:runId/artifacts", runController.getRunArtifacts);
router.get("/:runId/logs", runController.getRunLogs);
router.get("/:runId/plots/:filename", runController.getRunPlot);
router.get("/:runId/files/:filename", runController.getRunFile);
router.post("/:runId/swarm-simulation", async (req, res, next) => {
  try {
    const result = await swarmService.runSwarmSimulation(req.params.runId, req.body?.swarmConfig);
    res.status(200).json(result);
  } catch (error) {
    next(error);
  }
});
router.get("/:runId/swarm-summary", async (req, res, next) => {
  try {
    const result = await swarmService.readSwarmSummary(req.params.runId);
    res.json(result);
  } catch (error) {
    next(error);
  }
});
router.get("/:runId/swarm-trials", async (req, res, next) => {
  try {
    const trials = await swarmService.readSwarmTrials(req.params.runId);
    res.type("text/csv; charset=utf-8").send(trials ?? "");
  } catch (error) {
    next(error);
  }
});

module.exports = router;
