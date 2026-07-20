const Run = require("../models/Run");
const fileService = require("./fileService");
const csvInputService = require("./csvInput.service");
const scenarioConfig = require("./scenarioConfig.service");
const { createRunId } = require("../utils/ids");
const { getRunPaths } = require("../utils/paths");
const { validateClientId } = require("../validators/run.validator");

async function createQueuedRun(payload) {
  const clientId = validateClientId(payload && payload.clientId);
  const config = scenarioConfig.validateScenarioConfig(payload && payload.config);
  const runId = createRunId();
  const paths = getRunPaths(runId);

  await fileService.createRunDirectories(paths);
  await scenarioConfig.writeScenarioEnv(paths.scenarioConfigFile, config);

  const csvPayload = csvInputService.collectInputCsvPayload(config);
  if (Object.keys(csvPayload).length > 0) {
    await csvInputService.writeInputCsvFiles(paths.csvDir, csvPayload);
  }

  const run = await Run.create({
    runId,
    clientId,
    status: "queued",
    config,
    paths,
    startedAt: null,
    finishedAt: null,
    error: null
  });

  return {
    runId: run.runId,
    status: run.status
  };
}

module.exports = {
  createQueuedRun
};
