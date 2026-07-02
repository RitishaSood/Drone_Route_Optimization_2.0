const express = require("express");
const rateLimit = require("express-rate-limit");

const runController = require("../controllers/run.controller");

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
router.get("/:runId/logs", runController.getRunLogs);
router.get("/:runId/plots/:filename", runController.getRunPlot);
router.get("/:runId/files/:filename", runController.getRunFile);

module.exports = router;
