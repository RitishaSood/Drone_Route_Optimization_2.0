const fs = require("fs/promises");
const path = require("path");
const { spawnSync } = require("child_process");

const { getRunPaths } = require("../utils/paths");
const { validateRunId } = require("../validators/run.validator");

const PYTHON_EXECUTABLE = process.env.PYTHON_EXECUTABLE || "python";

function getRepoRoot() {
  return path.resolve(__dirname, "../../..");
}

async function ensureSwarmConfigFile(runId, config) {
  const paths = getRunPaths(runId);
  await fs.mkdir(paths.configDir, { recursive: true });
  const file = path.join(paths.configDir, "swarm_config.json");
  await fs.writeFile(file, JSON.stringify(config ?? {}, null, 2), "utf8");
  return file;
}

async function runSwarmSimulation(runId, config) {
  validateRunId(runId);
  const paths = getRunPaths(runId);
  const configFile = await ensureSwarmConfigFile(runId, config);
  const args = [
    "-m",
    "pipeline.swarm_simulation.main",
    "--run-dir",
    paths.runDir,
    "--config-file",
    configFile,
  ];
  const result = spawnSync(PYTHON_EXECUTABLE, args, {
    cwd: getRepoRoot(),
    encoding: "utf8",
    env: {
      ...process.env,
      PYTHONPATH: [getRepoRoot(), process.env.PYTHONPATH].filter(Boolean).join(path.delimiter),
    },
    maxBuffer: 10 * 1024 * 1024,
  });

  if (result.status !== 0) {
    const error = new Error(result.stderr || result.stdout || "Swarm simulation failed");
    error.statusCode = 500;
    throw error;
  }

  return readSwarmSummary(runId);
}

async function readSwarmSummary(runId) {
  validateRunId(runId);
  const paths = getRunPaths(runId);
  const summaryFile = path.join(paths.runDir, "outputs", "swarm_monte_carlo_summary.json");
  const trialsFile = path.join(paths.runDir, "outputs", "swarm_monte_carlo_trials.csv");

  let summary = null;
  let trials = null;
  try {
    summary = JSON.parse(await fs.readFile(summaryFile, "utf8"));
  } catch {
    summary = null;
  }

  try {
    trials = await fs.readFile(trialsFile, "utf8");
  } catch {
    trials = null;
  }

  return {
    runId,
    available: Boolean(summary),
    summary: summary?.summary ?? [],
    config: summary?.config ?? null,
    trialsAvailable: Boolean(trials),
  };
}

async function readSwarmTrials(runId) {
  validateRunId(runId);
  const paths = getRunPaths(runId);
  const file = path.join(paths.runDir, "outputs", "swarm_monte_carlo_trials.csv");
  try {
    return await fs.readFile(file, "utf8");
  } catch {
    return null;
  }
}

module.exports = {
  runSwarmSimulation,
  readSwarmSummary,
  readSwarmTrials,
};
