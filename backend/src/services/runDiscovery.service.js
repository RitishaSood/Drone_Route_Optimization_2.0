const fs = require("fs/promises");
const path = require("path");

const SAFE_RUN_ID = /^[A-Za-z0-9_-]+$/;
const RUN_DISCOVERY_TTL_MS = 5000;
let runDiscoveryCache = { expiresAt: 0, value: [] };

function getRunsRoot() {
  return path.resolve(process.env.RUNS_DIR || path.join(process.cwd(), "../runs"));
}

async function discoverRuns() {
  const now = Date.now();
  if (runDiscoveryCache.expiresAt > now) {
    return runDiscoveryCache.value;
  }

  const runsRoot = getRunsRoot();
  let entries = [];

  try {
    entries = await fs.readdir(runsRoot, { withFileTypes: true });
  } catch {
    runDiscoveryCache = { expiresAt: now + RUN_DISCOVERY_TTL_MS, value: [] };
    return [];
  }

  const discovered = [];

  for (const entry of entries) {
    if (!entry.isDirectory() || entry.name.startsWith(".")) continue;
    if (!SAFE_RUN_ID.test(entry.name)) continue;

    const runPath = path.join(runsRoot, entry.name);
    const csvPath = path.join(runPath, "csv");
    const outputsPath = path.join(runPath, "outputs");
    const plotsPath = path.join(runPath, "plots");

    discovered.push({
      runId: entry.name,
      path: runPath,
      isSeedRun: /^seed_\d+$/.test(entry.name),
      seedNumber: Number.parseInt(entry.name.replace(/^seed_/, ""), 10),
      hasCsv: await exists(csvPath),
      hasOutputs: await exists(outputsPath),
      hasPlots: await exists(plotsPath)
    });
  }

  runDiscoveryCache = { expiresAt: now + RUN_DISCOVERY_TTL_MS, value: discovered };
  return discovered;
}

async function exists(targetPath) {
  try {
    const stat = await fs.stat(targetPath);
    return stat.isDirectory();
  } catch {
    return false;
  }
}

function safeResolveRunFolder(runId) {
  if (typeof runId !== "string" || !SAFE_RUN_ID.test(runId)) {
    const error = new Error("Invalid runId");
    error.statusCode = 400;
    throw error;
  }

  const runsRoot = getRunsRoot();
  const resolved = path.resolve(runsRoot, runId);
  if (!resolved.startsWith(`${runsRoot}${path.sep}`)) {
    const error = new Error("Invalid runId");
    error.statusCode = 400;
    throw error;
  }
  return resolved;
}

module.exports = {
  discoverRuns,
  getRunsRoot,
  safeResolveRunFolder
};
